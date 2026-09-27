package io.github.gzpagg.envevidence;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.util.AtomicFile;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.WindowInsets;
import android.widget.FrameLayout;
import androidx.webkit.WebViewAssetLoader;
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader;
import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.text.PDFTextStripper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** All files stay in private app storage; only an explicit extract call uses the network. */
public class MainActivity extends Activity {
    private static final String HOME = "https://appassets.androidplatform.net/assets/index.html";
    private static final int LIMIT = 30 * 1024 * 1024;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private WebView web;
    private AtomicFile storage;
    private String pendingId, pendingMethod;
    private JSONObject pendingPayload;
    private boolean unreadable;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        PDFBoxResourceLoader.init(getApplicationContext());
        storage = new AtomicFile(new File(getFilesDir(), "workspace.json"));
        FrameLayout root = new FrameLayout(this);
        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(-1, -1));
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets i = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                v.setPadding(i.left, i.top, i.right, i.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        setContentView(root);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportMultipleWindows(false);
        web.setSaveEnabled(false);
        WebView.setWebContentsDebuggingEnabled(false);
        final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this)).build();
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                WebResourceResponse response = loader.shouldInterceptRequest(r.getUrl());
                return response != null ? response : new WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", null, new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return !HOME.equals(r.getUrl().toString());
            }
        });
        web.addJavascriptInterface(new Bridge(), "Android");
        web.loadUrl(HOME);
        if (android.os.Build.VERSION.SDK_INT >= 33) getOnBackInvokedDispatcher().registerOnBackInvokedCallback(0, this::goBack);
    }

    private void goBack() { web.evaluateJavascript("window.goBack ? window.goBack() : false", value -> { if (!"true".equals(value)) finish(); }); }
    @Override public void onBackPressed() { goBack(); }

    private void reply(String id, Object data, String error) {
        runOnUiThread(() -> {
            if (isFinishing() || isDestroyed()) return;
            JSONObject result = new JSONObject();
            try { result.put("id", id); result.put("data", data == null ? JSONObject.NULL : data); result.put("error", error == null ? JSONObject.NULL : error); }
            catch (Exception ignored) { return; }
            web.evaluateJavascript("window.nativeReply(" + result + ")", null);
        });
    }

    private byte[] read(InputStream input, int limit) throws Exception {
        if (input == null) throw new Exception("file");
        try (InputStream in = input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192]; int n;
            while ((n = in.read(buf)) != -1) { if (out.size() + n > limit) throw new Exception("tooLarge"); out.write(buf, 0, n); }
            return out.toByteArray();
        }
    }

    private class Bridge {
        @JavascriptInterface public void request(String id, String method, String raw) {
            if (id == null || !id.matches("[a-zA-Z0-9_-]{1,80}")) return;
            worker.execute(() -> {
                try {
                    JSONObject p = new JSONObject(raw);
                    switch (method) {
                        case "load":
                            if (!storage.getBaseFile().exists() && !new File(storage.getBaseFile()+".bak").exists()) { reply(id, null, null); break; }
                            try { reply(id, new JSONObject(new String(read(storage.openRead(), LIMIT), StandardCharsets.UTF_8)), null); }
                            catch (Exception e) { unreadable = true; reply(id, null, "loadFailed"); }
                            break;
                        case "save":
                            if (unreadable) throw new Exception("loadFailed");
                            JSONObject state = p.getJSONObject("state");
                            if (!state.getString("format").equals("envevidence-android") || state.getInt("schema_version") != 1) throw new Exception("invalid");
                            byte[] bytes = state.toString().getBytes(StandardCharsets.UTF_8);
                            if (bytes.length > LIMIT) throw new Exception("tooLarge");
                            FileOutputStream out = null;
                            try { out = storage.startWrite(); out.write(bytes); storage.finishWrite(out); }
                            catch (Exception e) { if (out != null) storage.failWrite(out); throw new Exception("saveFailed"); }
                            reply(id, true, null); break;
                        case "pickPdf": case "import": case "export":
                            runOnUiThread(() -> choose(id, method, p)); break;
                        case "extract": reply(id, extract(p), null); break;
                        case "openLink":
                            Uri uri = Uri.parse(p.getString("url"));
                            if (!("https".equals(uri.getScheme()) || "http".equals(uri.getScheme())) || uri.getHost() == null) throw new Exception("invalid");
                            runOnUiThread(() -> {
                                try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); reply(id, true, null); }
                                catch (Exception e) { reply(id, null, "file"); }
                            }); break;
                        default: throw new Exception("invalid");
                    }
                } catch (Exception e) {
                    String code = e.getMessage();
                    if (code == null || !code.matches("(invalid|tooLarge|tooManyPages|encrypted|noText|file|saveFailed|loadFailed|network|http[0-9]{3})")) code = method.equals("extract") ? "network" : "file";
                    reply(id, null, code);
                }
            });
        }
    }

    private void choose(String id, String method, JSONObject p) {
        if (pendingId != null) { reply(id, null, "busy"); return; }
        Intent intent;
        if (method.equals("export")) {
            intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(p.optString("mime", "application/json"));
            intent.putExtra(Intent.EXTRA_TITLE, p.optString("name", "envevidence.json").replaceAll("[^a-zA-Z0-9._-]", "_"));
        } else intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(method.equals("pickPdf") ? "application/pdf" : "*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        pendingId = id; pendingMethod = method; pendingPayload = p;
        try { startActivityForResult(intent, 1); }
        catch (Exception e) { pendingId = null; pendingPayload = null; reply(id, null, "file"); }
    }

    @Override public void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != 1 || pendingId == null) return;
        String id = pendingId, method = pendingMethod; JSONObject payload = pendingPayload;
        pendingId = null; pendingPayload = null;
        if (result != RESULT_OK || data == null || data.getData() == null) { reply(id, null, "cancelled"); return; }
        Uri uri = data.getData();
        worker.execute(() -> {
            try {
                if (method.equals("export")) {
                    try (OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                        if (out == null) throw new Exception("file");
                        out.write(payload.getString("text").getBytes(StandardCharsets.UTF_8));
                    }
                    reply(id, true, null);
                } else {
                    byte[] bytes = read(getContentResolver().openInputStream(uri), LIMIT);
                    if (method.equals("import")) reply(id, new JSONObject(new String(bytes, StandardCharsets.UTF_8)), null);
                    else reply(id, parsePdf(bytes, filename(uri), payload.optString("role", "main")), null);
                }
            } catch (Exception e) {
                String message = e.getMessage();
                reply(id, null, message != null && message.matches("tooLarge|tooManyPages|encrypted|noText") ? message : "file");
            }
        });
    }

    private String filename(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) { /* Only a display name, never a filesystem path. */ }
        return "paper.pdf";
    }

    JSONObject parsePdf(byte[] bytes, String name, String role) throws Exception {
        String id = UUID.randomUUID().toString().replace("-", "");
        try (PDDocument doc = PDDocument.load(bytes)) {
            if (doc.isEncrypted() && !doc.getCurrentAccessPermission().canExtractContent()) throw new Exception("encrypted");
            int pages = doc.getNumberOfPages();
            if (pages > 250) throw new Exception("tooManyPages");
            JSONArray blocks = new JSONArray(), warnings = new JSONArray();
            PDFTextStripper stripper = new PDFTextStripper(); stripper.setSortByPosition(true);
            int chars = 0;
            for (int page = 1; page <= pages; page++) {
                stripper.setStartPage(page); stripper.setEndPage(page);
                String text = stripper.getText(doc).trim(); chars += text.length();
                if (chars > 1000000) throw new Exception("tooLarge");
                if (text.length() < 20) warnings.put("Page " + page + ": little or no extractable text; inspect the original PDF.");
                blocks.put(new JSONObject().put("id", id+":p"+page).put("page", page).put("text", text));
            }
            if (chars == 0) throw new Exception("noText");
            StringBuilder hash = new StringBuilder();
            for (byte b : MessageDigest.getInstance("SHA-256").digest(bytes)) hash.append(String.format("%02x", b & 255));
            return new JSONObject().put("id",id).put("filename",name).put("sha256",hash.toString()).put("role",role)
                .put("page_count",pages).put("blocks",blocks).put("warnings",warnings).put("parser","pdfbox-android-2.0.27.0");
        } catch (com.tom_roush.pdfbox.pdmodel.encryption.InvalidPasswordException e) { throw new Exception("encrypted"); }
    }

    private JSONObject extract(JSONObject p) throws Exception {
        String provider = p.getString("provider"), key = p.getString("key");
        if (!(provider.equals("openai") || provider.equals("anthropic")) || key.isBlank() || key.contains("\n") || key.contains("\r")) throw new Exception("invalid");
        String endpoint = provider.equals("openai") ? "https://api.openai.com/v1/responses" : "https://api.anthropic.com/v1/messages";
        HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
        try {
            connection.setRequestMethod("POST"); connection.setDoOutput(true); connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(30000); connection.setReadTimeout(120000);
            connection.setRequestProperty("Content-Type", "application/json");
            if (provider.equals("openai")) connection.setRequestProperty("Authorization", "Bearer " + key);
            else { connection.setRequestProperty("x-api-key",key); connection.setRequestProperty("anthropic-version","2023-06-01"); }
            byte[] body = p.getJSONObject("body").toString().getBytes(StandardCharsets.UTF_8);
            if (body.length > 2000000) throw new Exception("tooLarge");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream out = connection.getOutputStream()) { out.write(body); }
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) throw new Exception("http"+status);
            return new JSONObject(new String(read(connection.getInputStream(), 4*1024*1024), StandardCharsets.UTF_8));
        } finally { connection.disconnect(); }
    }

    @Override public void onDestroy() {
        if (web != null) { web.removeJavascriptInterface("Android"); web.destroy(); }
        worker.shutdown(); super.onDestroy();
    }
}

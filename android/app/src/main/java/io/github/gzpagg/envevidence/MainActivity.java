package io.github.gzpagg.envevidence;

import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;
import android.content.Intent;
import android.content.ClipData;
import android.content.pm.PackageManager;
import android.provider.MediaStore;
import android.provider.Settings;
import android.speech.RecognizerIntent;
import android.Manifest;
import java.util.ArrayList;
import androidx.core.content.FileProvider;
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
public class MainActivity extends ComponentActivity {
    private static final String HOME = "https://appassets.androidplatform.net/assets/index.html";
    private static final int LIMIT = 30 * 1024 * 1024;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private WebView web;
    private AtomicFile storage;
    private String pendingId, pendingMethod;
    private JSONObject pendingPayload;
    private boolean unreadable;
    private boolean openTimers;
    private LabAudio audio;
    private volatile boolean audioForeground;
    private String microphoneRequest, microphoneRecord, speechRequest, speechLanguage;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        openTimers=getIntent().getBooleanExtra("openTimers",false);
        PDFBoxResourceLoader.init(getApplicationContext());
        storage = new AtomicFile(new File(getFilesDir(), "workspace.json"));
        audio = new LabAudio(this, (notice, state) -> runOnUiThread(() -> {
            if(web!=null&&!isDestroyed())web.evaluateJavascript("window.labAudioStopped ? window.labAudioStopped("+notice+") : (window.labReload && window.labReload())",null);
        }));
        if(saved!=null&&saved.containsKey("photoMethod"))try{pendingId=saved.getString("photoRequest");pendingMethod=saved.getString("photoMethod");pendingPayload=new JSONObject(saved.getString("photoPayload"));}catch(Exception ignored){pendingId=null;}
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
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .addPathHandler("/photos/", path -> {
                try{return new WebResourceResponse(path.endsWith(".png")?"image/png":path.endsWith(".webp")?"image/webp":"image/jpeg",null,new java.io.FileInputStream(LabPhotos.file(this,path)));}
                catch(Exception e){return null;}
            })
            .addPathHandler("/audio/", path -> LabAudio.response(this,path,null,"GET")).build();
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                Uri u=r.getUrl();
                if("https".equals(u.getScheme())&&"appassets.androidplatform.net".equals(u.getHost())&&u.getPort()==-1&&u.getPath()!=null&&u.getPath().startsWith("/audio/")){
                    String range=null;for(java.util.Map.Entry<String,String> h:r.getRequestHeaders().entrySet())if("range".equalsIgnoreCase(h.getKey()))range=h.getValue();
                    return LabAudio.response(MainActivity.this,u.getPath().substring(7),range,r.getMethod());
                }
                WebResourceResponse response = loader.shouldInterceptRequest(u);
                return response != null ? response : new WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", null, new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return !HOME.equals(r.getUrl().toString());
            }
        });
        web.addJavascriptInterface(new Bridge(), "Android");
        web.loadUrl(HOME);
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() { goBack(); }
        });
    }

    private void goBack() { web.evaluateJavascript("window.goBack ? window.goBack() : false", value -> { if (!"true".equals(value)) finish(); }); }

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
                            recoverCamera();
                            audio.recover();
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
                            LabStore.save(MainActivity.this,state);
                            LabAlarms.sync(MainActivity.this);
                            reply(id, true, null); break;
                        case "clock":
                            JSONObject clock=LabStore.clock(MainActivity.this).put("exact",LabAlarms.exact(MainActivity.this)).put("notifications",LabAlarms.notifications(MainActivity.this)).put("openTimers",openTimers);
                            openTimers=false;
                            reply(id,clock,null);break;
                        case "checkAlarms":reply(id,LabAlarms.fireDue(MainActivity.this),null);break;
                        case "enableAlerts":runOnUiThread(()->{enableAlerts();reply(id,true,null);});break;
                        case "capturePhoto": case "pickPhoto": case "backupLab": case "importLab":
                        case "pickPdf": case "import": case "export":
                            runOnUiThread(() -> choose(id, method, p)); break;
                        case "startAudio":runOnUiThread(()->startAudio(id,p));break;
                        case "stopAudio":reply(id,audio.stop("user"),null);break;
                        case "cancelAudio":audio.cancel();reply(id,true,null);break;
                        case "audioStatus":audio.recover();reply(id,audio.status(),null);break;
                        case "speechToText":runOnUiThread(()->speechToText(id,p));break;
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
                    if (code == null || !code.matches("(invalid|tooLarge|tooManyPages|encrypted|noText|file|saveFailed|loadFailed|network|photoConflict|missingPhoto|missingAudio|audioConflict|mediaChecksum|imageFormat|micDenied|micBlocked|audioBusy|audioNotRecording|audioTooShort|audioFailed|audioSaveFailed|audioInactive|speechUnavailable|speechCancelled|speechEmpty|speechBusy|http[0-9]{3})")) code = method.equals("extract") ? "network" : "file";
                    reply(id, null, code);
                }
            });
        }
    }

    private void choose(String id, String method, JSONObject p) {
        if (pendingId != null) { reply(id, null, "busy"); return; }
        Intent intent;
        if(method.equals("capturePhoto")){
            try{
                String photoId=UUID.randomUUID().toString().replace("-","");p.put("photoId",photoId);
                File f=LabPhotos.file(this,photoId+".jpg");Uri uri=FileProvider.getUriForFile(this,getPackageName()+".photos",f);
                intent=new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT,uri).addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_READ_URI_PERMISSION);
                intent.setClipData(ClipData.newRawUri("photo",uri));
                getSharedPreferences("lab-camera",0).edit().putString("pending",p.toString()).commit();
            }catch(Exception e){reply(id,null,"file");return;}
        }else if(method.equals("backupLab")){
            intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/zip").putExtra(Intent.EXTRA_TITLE,"envevidence-lab-backup.zip");intent.addCategory(Intent.CATEGORY_OPENABLE);
        }else if (method.equals("export")) {
            intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(p.optString("mime", "application/json"));
            intent.putExtra(Intent.EXTRA_TITLE, p.optString("name", "envevidence.json").replaceAll("[^a-zA-Z0-9._-]", "_"));
        } else intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(method.equals("pickPdf") ? "application/pdf" : method.equals("pickPhoto")?"image/*":"*/*");
        if(!method.equals("capturePhoto"))intent.addCategory(Intent.CATEGORY_OPENABLE);
        pendingId = id; pendingMethod = method; pendingPayload = p;
        try { startActivityForResult(intent, 1); }
        catch (Exception e) { pendingId = null; pendingPayload = null; getSharedPreferences("lab-camera",0).edit().remove("pending").apply();reply(id, null, "file"); }
    }

    @Override public void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if(request==42){
            String id=speechRequest,language=speechLanguage;speechRequest=null;speechLanguage=null;if(id==null)return;
            if(result!=RESULT_OK){reply(id,null,"speechCancelled");return;}
            ArrayList<String> choices=data==null?null:data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if(choices==null||choices.isEmpty()||choices.get(0)==null||choices.get(0).trim().isEmpty()){reply(id,null,"speechEmpty");return;}
            try{String text=choices.get(0).trim();if(text.length()>20000)throw new Exception("tooLarge");reply(id,new JSONObject().put("text",text).put("language",language),null);}catch(Exception e){reply(id,null,"tooLarge");}return;
        }
        if (request != 1 || pendingId == null) return;
        String id = pendingId, method = pendingMethod; JSONObject payload = pendingPayload;
        pendingId = null; pendingPayload = null;
        if (result != RESULT_OK || (!method.equals("capturePhoto")&&(data == null || data.getData() == null))) { if(method.equals("capturePhoto"))getSharedPreferences("lab-camera",0).edit().remove("pending").apply();reply(id, null, "cancelled"); return; }
        Uri uri = data==null?null:data.getData();
        worker.execute(() -> {
            try {
                if(method.equals("capturePhoto")||method.equals("pickPhoto")){
                    JSONObject photo;
                    if(method.equals("capturePhoto")){String photoId=payload.getString("photoId");photo=LabPhotos.ingest(this,read(new java.io.FileInputStream(LabPhotos.file(this,photoId+".jpg")),LIMIT),"camera.jpg",photoId);}
                    else photo=LabPhotos.ingest(this,read(getContentResolver().openInputStream(uri),LIMIT),filename(uri),null);
                    JSONObject updated=LabPhotos.attach(this,payload.getString("recordId"),photo);getSharedPreferences("lab-camera",0).edit().remove("pending").apply();reply(id,updated,null);
                    runOnUiThread(()->web.evaluateJavascript("window.labReload && window.labReload()",null));
                }else if(method.equals("backupLab")){LabPhotos.backup(this,uri,payload.optString("experimentId",null));reply(id,true,null);}
                else if(method.equals("importLab")){reply(id,LabPhotos.restore(this,uri),null);}
                else if (method.equals("export")) {
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
                reply(id, null, message != null && message.matches("tooLarge|tooManyPages|encrypted|noText|photoConflict|missingPhoto|missingAudio|audioConflict|mediaChecksum|imageFormat|invalid|backupLimit") ? message : "file");
            }
        });
    }

    private void recoverCamera() throws Exception {
        String pending=getSharedPreferences("lab-camera",0).getString("pending",null);if(pending==null||"capturePhoto".equals(pendingMethod))return;
        JSONObject p=new JSONObject(pending);File f=LabPhotos.file(this,p.getString("photoId")+".jpg");
        if(f.exists()&&f.length()>0){JSONObject photo=LabPhotos.ingest(this,LabStore.read(new java.io.FileInputStream(f),LIMIT),"camera.jpg",p.getString("photoId"));LabPhotos.attach(this,p.getString("recordId"),photo);getSharedPreferences("lab-camera",0).edit().remove("pending").commit();}
    }
    private void enableAlerts(){
        if(android.os.Build.VERSION.SDK_INT>=33&&checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},40);return;}
        if(android.os.Build.VERSION.SDK_INT>=31&&!LabAlarms.exact(this)){startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,Uri.parse("package:"+getPackageName())));return;}
        if(!LabAlarms.notifications(this))startActivity(new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE,getPackageName()));
        LabAlarms.sync(this);
    }
    private void startAudio(String id,JSONObject p){
        if(microphoneRequest!=null||speechRequest!=null||pendingId!=null||audio.active()){reply(id,null,"audioBusy");return;}
        String recordId=p.optString("recordId",null);if(recordId==null||!recordId.matches("[a-f0-9]{32}")){reply(id,null,"invalid");return;}
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            microphoneRequest=id;microphoneRecord=recordId;requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},41);return;
        }
        worker.execute(()->{try{synchronized(audio){if(!audioForeground)throw new Exception("audioInactive");audio.recover();reply(id,audio.start(recordId),null);}}catch(Exception e){reply(id,null,audioError(e));}});
    }
    private String audioError(Exception e){String code=e.getMessage();return code!=null&&code.matches("invalid|micDenied|audioBusy|audioNotRecording|audioTooShort|audioSaveFailed|audioConflict|audioInactive")?code:"audioFailed";}
    private void speechToText(String id,JSONObject p){
        if(speechRequest!=null||microphoneRequest!=null||pendingId!=null||audio.active()){reply(id,null,"speechBusy");return;}
        String language=p.optString("language","en");if(!language.equals("en")&&!language.equals("zh")){reply(id,null,"invalid");return;}
        Intent intent=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,language.equals("zh")?"zh-CN":"en-US").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);
        if(intent.resolveActivity(getPackageManager())==null){reply(id,null,"speechUnavailable");return;}
        speechRequest=id;speechLanguage=language;
        try{startActivityForResult(intent,42);}catch(Exception e){speechRequest=null;speechLanguage=null;reply(id,null,"speechUnavailable");}
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){
        super.onRequestPermissionsResult(request,permissions,grants);
        if(request==40&&grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED)enableAlerts();
        if(request==41){String id=microphoneRequest,recordId=microphoneRecord;microphoneRequest=null;microphoneRecord=null;if(id==null)return;if(grants.length==0||grants[0]!=PackageManager.PERMISSION_GRANTED){reply(id,null,grants.length==0||shouldShowRequestPermissionRationale(Manifest.permission.RECORD_AUDIO)?"micDenied":"micBlocked");return;}try{startAudio(id,new JSONObject().put("recordId",recordId));}catch(Exception e){reply(id,null,"audioFailed");}}
    }
    @Override public void onSaveInstanceState(Bundle out){if(pendingId!=null&&("capturePhoto".equals(pendingMethod)||"pickPhoto".equals(pendingMethod))){out.putString("photoRequest",pendingId);out.putString("photoMethod",pendingMethod);out.putString("photoPayload",pendingPayload.toString());}super.onSaveInstanceState(out);}
    @Override protected void onResume(){super.onResume();audioForeground=true;worker.execute(()->LabAlarms.sync(this));if(web!=null){web.onResume();web.evaluateJavascript("window.labResume && window.labResume()",null);}}
    @Override protected void onStop(){audioForeground=false;if(audio!=null)audio.stopForBackground();super.onStop();}
    @Override protected void onPause(){if(web!=null)web.onPause();super.onPause();}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);if(web!=null)web.evaluateJavascript("window.labOpenTimers && window.labOpenTimers()",null);}

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
        if (!(provider.equals("openai") || provider.equals("anthropic")) || key.trim().isEmpty() || key.contains("\n") || key.contains("\r")) throw new Exception("invalid");
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
        if(audio!=null)audio.stopForBackground();
        if (web != null) { web.removeJavascriptInterface("Android"); web.destroy(); }
        worker.shutdown(); super.onDestroy();
    }
}

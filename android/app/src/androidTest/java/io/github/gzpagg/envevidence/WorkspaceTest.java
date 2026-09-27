package io.github.gzpagg.envevidence;

import android.webkit.WebView;
import android.view.ViewGroup;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class WorkspaceTest {
    private String js(ActivityScenario<MainActivity> scenario, String script) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<String> result = new AtomicReference<>();
        scenario.onActivity(activity -> {
            ViewGroup root = activity.findViewById(android.R.id.content);
            WebView web = (WebView) ((ViewGroup) root.getChildAt(0)).getChildAt(0);
            web.evaluateJavascript(script, value -> { result.set(value); done.countDown(); });
        });
        assertTrue("JavaScript callback", done.await(10, TimeUnit.SECONDS));
        return result.get();
    }
    private void ready(ActivityScenario<MainActivity> s, String condition) throws Exception {
        for (int i=0;i<100;i++) { if ("true".equals(js(s, condition))) return; Thread.sleep(100); }
        fail("UI condition not reached: "+condition);
    }
    private void shot(ActivityScenario<MainActivity> s, String name) throws Exception {
        ready(s, "getComputedStyle(document.querySelector('#notice')).display==='none'");
        CountDownLatch painted = new CountDownLatch(1);
        s.onActivity(activity -> {
            ViewGroup root = activity.findViewById(android.R.id.content);
            WebView web = (WebView) ((ViewGroup) root.getChildAt(0)).getChildAt(0);
            web.postVisualStateCallback(System.nanoTime(), new WebView.VisualStateCallback() {
                @Override public void onComplete(long requestId) {
                    web.postOnAnimation(() -> web.postOnAnimation(painted::countDown));
                    web.invalidate();
                }
            });
        });
        assertTrue("WebView has presented the requested page", painted.await(15, TimeUnit.SECONDS));
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
        Thread.sleep(500); // Let SurfaceFlinger present the already synchronized frame.
        // Gradle uninstalls the tested app after the run. Preserve synthetic screenshots
        // outside its private directory using the test runner's shell identity only.
        // executeShellCommand runs a program directly; shell operators are not interpreted.
        shell("mkdir -p /sdcard/Download/envevidence-screenshots");
        String path = "/sdcard/Download/envevidence-screenshots/"+name+".png";
        shell("screencap -p "+path);
        String size = shell("wc -c "+path).trim().split("\\s+")[0];
        assertTrue("Screenshot must contain image bytes", Long.parseLong(size)>1000);
    }
    private String shell(String command) throws Exception {
        android.os.ParcelFileDescriptor pipe = InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand(command);
        try (java.io.InputStream in = new android.os.ParcelFileDescriptor.AutoCloseInputStream(pipe)) {
            return new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        }
    }
    @Test public void offlineWorkspacePersistsAndEvidenceStaysTraceable() throws Exception {
        try (ActivityScenario<MainActivity> s = ActivityScenario.launch(MainActivity.class)) {
            ready(s, "!!document.querySelector('nav')");
            js(s,"document.querySelector('[data-to=settings]').click()");
            js(s,"document.querySelector('[data-action=demo]').click()");
            ready(s,"state.workspace.demo_loaded && state.projects.length===1");
            js(s,"navigate('home')"); shot(s,"home-en");
            js(s,"navigate('learning'); document.querySelector('[data-action=step]').click()");
            ready(s,"state.workspace.goals[0].steps[0].done===false");
            js(s,"navigate('tasks'); document.querySelector('select[data-action=taskStatus]').value='todo'; document.querySelector('select[data-action=taskStatus]').dispatchEvent(new Event('change',{bubbles:true}))");
            ready(s,"state.workspace.tasks[0].status==='todo'");
            js(s,"navigate('notes'); document.querySelector('[data-action=archive]').click()");
            ready(s,"state.workspace.notes[0].archived===true");
            js(s,"document.querySelector('[data-value=archived]').click(); document.querySelector('[data-action=archive]').click()");
            ready(s,"state.workspace.notes[0].archived===false");
            js(s,"navigate('settings')"); shot(s,"settings-en");
            js(s,"document.querySelector('[name=language]').value='zh'; document.querySelector('#settings-form').requestSubmit()");
            ready(s,"state.workspace.preferences.language==='zh'");
            shot(s,"settings-zh");
            js(s,"navigate('home')"); shot(s,"home-zh");
            s.recreate(); ready(s,"!!document.querySelector('nav') && state.workspace.preferences.language==='zh'");
            assertEquals("true",js(s,"state.workspace.goals[0].steps[0].done===false && state.workspace.tasks[0].status==='todo' && state.workspace.notes[0].archived===false"));
            js(s,"projectId=state.projects[0].id; navigate('evidence'); review(state.projects[0].experiments[0].id,state.projects[0].experiments[0].fields[0].id)");
            ready(s,"!!document.querySelector('dialog[open]')"); shot(s,"review-zh");
            js(s,"document.querySelector('[name=reviewer]').value='Synthetic reviewer'; document.querySelector('[name=reason]').value='Checked against the synthetic original'; document.querySelector('[name=status]').value='verified'; document.querySelector('dialog form').requestSubmit()");
            ready(s,"state.projects[0].experiments[0].fields[0].revisions.length===1");
            assertEquals("true",js(s,"state.projects[0].experiments[0].fields[0].revisions[0].status==='verified'"));
            js(s,"navigate('settings'); document.querySelector('[name=language]').value='en'; document.querySelector('#settings-form').requestSubmit()");
            ready(s,"state.workspace.preferences.language==='en'");
            js(s,"navigate('evidence'); review(state.projects[0].experiments[0].id,state.projects[0].experiments[0].fields[0].id)"); shot(s,"review-en");
            AtomicReference<Exception> error = new AtomicReference<>();
            s.onActivity(a -> {
                try {
                    byte[] pdf=a.getAssets().open("synthetic_main.pdf").readAllBytes();
                    JSONObject doc=a.parsePdf(pdf,"synthetic_main.pdf","main");
                    assertTrue(doc.getInt("page_count")>0);
                    assertTrue(doc.getJSONArray("blocks").toString().contains("Trial A"));
                    assertEquals(64,doc.getString("sha256").length());
                } catch(Exception e) { error.set(e); }
            });
            if(error.get()!=null)throw error.get();
        }
    }
}

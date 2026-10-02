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
        // The stock emulator launcher occasionally raises an ANR during cold boot.
        // Close only that external launcher; never hide an ANR from the tested app.
        android.view.accessibility.AccessibilityNodeInfo active=InstrumentationRegistry.getInstrumentation().getUiAutomation().getRootInActiveWindow();
        if(active!=null&&!active.findAccessibilityNodeInfosByText("Quickstep isn't responding").isEmpty()) {
            shell("am force-stop com.android.launcher3");
            InstrumentationRegistry.getInstrumentation().waitForIdleSync();
        }
        boolean foreground=false;
        for(int i=0;i<30;i++) {
            active=InstrumentationRegistry.getInstrumentation().getUiAutomation().getRootInActiveWindow();
            if(active!=null&&"io.github.gzpagg.envevidence".contentEquals(active.getPackageName())) {foreground=true;break;}
            Thread.sleep(100);
        }
        assertTrue("Screenshots must show the app without an external dialog",foreground);
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
    @Test public void peakAreaImportKeepsSampleAlignmentOnAndroid() throws Exception {
        android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        JSONObject clean=new JSONObject("{\"format\":\"envevidence-android\",\"schema_version\":1,\"workspace\":{\"schema_version\":1,\"preferences\":{\"language\":\"en\",\"palette\":\"clay\",\"accent\":\"#A65338\",\"background\":\"#F7F5F0\",\"order\":[\"evidence\",\"learning\",\"tasks\",\"notes\"],\"hidden\":[]},\"goals\":[],\"tasks\":[],\"notes\":[]},\"projects\":[]}");
        LabStore.save(context,clean);
        try(ActivityScenario<MainActivity> s=ActivityScenario.launch(MainActivity.class)) {
            ready(s,"!!document.querySelector('nav') && !!state.lab");
            js(s,"navigate('my');document.querySelector('[data-lab=labDemo]').click()");
            ready(s,"state.lab.demo_loaded && state.lab.samples.length===5");
            js(s,"experimentId=state.lab.experiments[0].id;navigate('experiment');areasForm(experimentId);window.beforeLC=JSON.stringify(state.lab.samples);(()=>{const f=document.querySelector('[name=areas]');f.value='10000\\nBAD\\n6400';f.dispatchEvent(new Event('input',{bubbles:true}));})()");
            assertEquals("true",js(s,"document.querySelector('dialog [type=submit]').disabled && document.querySelector('[data-bench-preview]').textContent.includes('S-003')"));
            js(s,"document.querySelector('dialog form').requestSubmit()");
            ready(s,"!busy");
            assertEquals("true",js(s,"JSON.stringify(state.lab.samples)===window.beforeLC"));
            js(s,"(()=>{const f=document.querySelector('[name=areas]');f.value='10000\\n\\n6400';f.dispatchEvent(new Event('input',{bubbles:true}));})()");
            assertEquals("true",js(s,"document.querySelector('dialog [type=submit]').disabled && document.querySelector('[data-bench-preview]').textContent.includes('S-003')"));
            js(s,"(()=>{const f=document.querySelector('[name=areas]');f.value='S-001 10000\\nS-002 8000\\nS-003 6400';f.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('dialog form').requestSubmit();})()");
            ready(s,"!document.querySelector('dialog') && !busy && state.lab.samples[1].c_over_c0===0.8 && state.lab.samples[2].c_over_c0===0.64");
            s.recreate();ready(s,"!!document.querySelector('nav') && state.lab.samples.length===5");
            assertEquals("true",js(s,"state.lab.samples[1].c_over_c0===0.8 && state.lab.samples[2].c_over_c0===0.64 && state.lab.samples[2].revisions.length>=2"));
        }
    }
    @Test public void labWorkspaceRetainsTimePhotosAndLegacyData() throws Exception {
        android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        JSONObject old=new JSONObject("{\"format\":\"envevidence-android\",\"schema_version\":1,\"workspace\":{\"schema_version\":1,\"preferences\":{\"language\":\"en\",\"palette\":\"forest\",\"accent\":\"#147D73\",\"background\":\"#F6F8F7\",\"order\":[\"evidence\",\"learning\",\"tasks\",\"notes\"],\"hidden\":[]},\"goals\":[],\"tasks\":[],\"notes\":[{\"id\":\"legacy-note\",\"title\":\"Old note\",\"body\":\"Preserve me\",\"pinned\":true,\"archived\":false,\"color\":\"sage\"}]},\"projects\":[]}");
        JSONObject evidence=new JSONObject(new String(context.getAssets().open("demo-project.json").readAllBytes(),java.nio.charset.StandardCharsets.UTF_8));
        old.getJSONArray("projects").put(evidence);LabStore.save(context,old);
        shell("pm grant io.github.gzpagg.envevidence android.permission.POST_NOTIFICATIONS");
        shell("appops set io.github.gzpagg.envevidence SCHEDULE_EXACT_ALARM allow");
        try (ActivityScenario<MainActivity> s = ActivityScenario.launch(MainActivity.class)) {
            ready(s,"!!document.querySelector('nav') && !!state.lab");
            assertEquals("true",js(s,"document.querySelectorAll('nav button').length===4 && !document.querySelector('header button') && state.workspace.notes[0].body==='Preserve me'"));
            assertEquals(evidence.toString(),LabStore.load(context).getJSONArray("projects").getJSONObject(0).toString());
            js(s,"navigate('my'); document.querySelector('[data-lab=labDemo]').click()");
            ready(s,"state.lab.demo_loaded && state.lab.experiments.length===1");
            js(s,"navigate('experiments')");shot(s,"lab-home-en");
            js(s,"navigate('timers')");shot(s,"lab-timers-en");
            js(s,"document.querySelector('[data-lab=addCount]').click()");ready(s,"state.lab.counters[0].value===3");
            js(s,"document.querySelector('[data-lab=undoCount]').click()");ready(s,"state.lab.counters[0].value===2");
            android.graphics.Bitmap fixture=android.graphics.Bitmap.createBitmap(700,420,android.graphics.Bitmap.Config.ARGB_8888);
            android.graphics.Canvas canvas=new android.graphics.Canvas(fixture);canvas.drawColor(android.graphics.Color.rgb(238,230,209));android.graphics.Paint paint=new android.graphics.Paint(3);paint.setColor(android.graphics.Color.rgb(168,131,64));canvas.drawCircle(230,200,90,paint);paint.setColor(android.graphics.Color.rgb(193,154,85));canvas.drawCircle(475,200,90,paint);paint.setColor(android.graphics.Color.rgb(69,60,42));paint.setTextSize(24);canvas.drawText("SYNTHETIC SAMPLE / NOT REAL DATA",90,370,paint);
            java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();fixture.compress(android.graphics.Bitmap.CompressFormat.PNG,100,bytes);fixture.recycle();
            JSONObject photo=LabPhotos.ingest(context,bytes.toByteArray(),"Synthetic sample.png",null);
            JSONObject updated=LabStore.load(context);String recordId=updated.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getString("id");LabPhotos.attach(context,recordId,photo);
            js(s,"labReload()");ready(s,"state.lab.records[0].photos.length===1");
            js(s,"navigate('records')");ready(s,"Array.from(document.querySelectorAll('.photo-grid img')).every(i=>i.complete&&i.naturalWidth>0)");shot(s,"lab-records-en");
            java.io.File archive=new java.io.File(context.getCacheDir(),"lab-backup.zip");LabPhotos.backup(context,android.net.Uri.fromFile(archive));
            try(java.util.zip.ZipFile z=new java.util.zip.ZipFile(archive)){assertArrayEquals(bytes.toByteArray(),z.getInputStream(z.getEntry("photos/"+photo.getString("id")+".png")).readAllBytes());assertNotNull(z.getEntry("workspace.json"));}
            JSONObject restored=LabPhotos.restore(context,android.net.Uri.fromFile(archive));assertEquals(recordId,restored.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getString("id"));
            assertTrue(restored.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("photos").getJSONObject(0).has("recorded_at"));
            java.io.File single=new java.io.File(context.getCacheDir(),"single-experiment.zip");LabPhotos.backup(context,android.net.Uri.fromFile(single),restored.getJSONObject("lab").getJSONArray("experiments").getJSONObject(0).getString("id"));
            JSONObject singleState=LabPhotos.restore(context,android.net.Uri.fromFile(single));assertEquals(0,singleState.getJSONArray("projects").length());assertEquals(0,singleState.getJSONObject("workspace").getJSONArray("notes").length());assertEquals(1,singleState.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("photos").length());assertEquals(5,singleState.getJSONObject("lab").getJSONArray("samples").length());
            js(s,"navigate('my')");shot(s,"lab-my-en");
            js(s,"navigate('appearance'); document.querySelector('[name=language]').value='zh'; document.querySelector('#settings-form').requestSubmit()");ready(s,"state.workspace.preferences.language==='zh'");
            js(s,"navigate('experiments')");shot(s,"lab-home-zh");js(s,"navigate('timers')");shot(s,"lab-timers-zh");js(s,"navigate('records')");ready(s,"Array.from(document.querySelectorAll('.photo-grid img')).every(i=>i.complete&&i.naturalWidth>0)");shot(s,"lab-records-zh");js(s,"navigate('my')");shot(s,"lab-my-zh");
            s.recreate();ready(s,"!!document.querySelector('nav') && state.workspace.preferences.language==='zh' && state.lab.records[0].photos.length===1");
            assertEquals("true",js(s,"state.workspace.notes[0].body==='Preserve me' && state.lab.counters[0].value===2 && !document.querySelector('header button')"));
            js(s,"(async()=>{await refreshClock();await commit(s=>{const t=L.timer(s.lab,{title:'Background alarm test',kind:'countdown',duration_ms:3000},labClock());L.operate(s.lab,t,'start',labClock());});window.alarmTestReady=true;})()");ready(s,"window.alarmTestReady===true");
            String timerId=LabStore.load(context).getJSONObject("lab").getJSONArray("timers").getJSONObject(0).getString("id");
            assertTrue("Exact alarms allowed in test device",LabAlarms.exact(context));
            s.moveToState(androidx.lifecycle.Lifecycle.State.CREATED);Thread.sleep(4500);
            assertTrue("Alarm delivered with activity in background",context.getSharedPreferences(LabAlarms.PREFS,0).getStringSet("delivered",java.util.Collections.emptySet()).contains(timerId+":0"));
            assertTrue("System notification posted",context.getSystemService(android.app.NotificationManager.class).getActiveNotifications().length>0);
            s.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED);ready(s,"L.elapsed(state.lab.timers[0],labClock())>=4000");
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
        // Launch with the notification extra through ActivityScenario itself. Replacing
        // an active scenario's Intent would discard its lifecycle-monitoring metadata.
        try(ActivityScenario<MainActivity> notification=ActivityScenario.launch(new android.content.Intent(context,MainActivity.class).putExtra("openTimers",true))) {
            ready(notification,"page==='timers' && !!document.querySelector('nav')");
        }
    }
}


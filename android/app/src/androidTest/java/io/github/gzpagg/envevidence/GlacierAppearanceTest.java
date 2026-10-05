package io.github.gzpagg.envevidence;

import android.view.ViewGroup;
import android.webkit.WebView;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class GlacierAppearanceTest {
    private String js(ActivityScenario<MainActivity> scenario, String script) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<String> value = new AtomicReference<>();
        scenario.onActivity(activity -> {
            ViewGroup root = activity.findViewById(android.R.id.content);
            WebView web = (WebView)((ViewGroup)root.getChildAt(0)).getChildAt(0);
            web.evaluateJavascript(script, result -> { value.set(result); done.countDown(); });
        });
        assertTrue("JavaScript callback", done.await(10, TimeUnit.SECONDS));
        return value.get();
    }
    private void ready(ActivityScenario<MainActivity> scenario, String condition) throws Exception {
        for (int i=0;i<100;i++) { if ("true".equals(js(scenario,condition))) return; Thread.sleep(100); }
        fail("UI condition not reached: "+condition);
    }
    @Test public void oldDefaultUpgradesAndMaterialChoiceSurvivesRestart() throws Exception {
        JSONObject prefs = new JSONObject().put("language","en").put("palette","mineral")
            .put("accent","#186B62").put("background","#F4F7F6")
            .put("order",new JSONArray().put("evidence").put("learning").put("tasks").put("notes"))
            .put("hidden",new JSONArray());
        JSONObject oldNote = new JSONObject().put("id","glacier-legacy-note").put("title","Original lab note")
            .put("body","Retain the exact original text").put("archived",false).put("pinned",true).put("color","sage");
        JSONObject old = new JSONObject().put("format","envevidence-android").put("schema_version",1)
            .put("projects",new JSONArray()).put("workspace",new JSONObject().put("schema_version",1)
            .put("preferences",prefs).put("goals",new JSONArray()).put("tasks",new JSONArray())
            .put("notes",new JSONArray().put(oldNote)));
        LabStore.save(InstrumentationRegistry.getInstrumentation().getTargetContext(),old);
        try(ActivityScenario<MainActivity> scenario=ActivityScenario.launch(MainActivity.class)) {
            ready(scenario,"!!document.querySelector('.lab-nav') && state.workspace.preferences.palette==='glacier'");
            assertEquals("true",js(scenario,"state.workspace.preferences.appearance_version===2 && state.workspace.notes[0].body==='Retain the exact original text'"));
            js(scenario,"navigate('appearance')");
            ready(scenario,"!!document.querySelector('#settings-form [name=reduce_transparency]')");
            js(scenario,"document.querySelector('#settings-form [name=reduce_transparency]').click();document.querySelector('#settings-form').requestSubmit()");
            ready(scenario,"state.workspace.preferences.reduce_transparency===true && !busy");
            ready(scenario,"getComputedStyle(document.querySelector('.lab-nav')).backdropFilter==='none'");
            scenario.recreate();
            ready(scenario,"!!document.querySelector('.lab-nav') && state.workspace.preferences.reduce_transparency===true");
            assertEquals("true",js(scenario,"state.workspace.preferences.palette==='glacier' && state.workspace.notes[0].body==='Retain the exact original text'"));
            js(scenario,"navigate('appearance');(()=>{const p=document.querySelector('#settings-form [name=palette]');p.value='mineral';p.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#settings-form').requestSubmit();})()");
            ready(scenario,"state.workspace.preferences.palette==='mineral' && !busy");
            scenario.recreate();
            ready(scenario,"!!document.querySelector('.lab-nav') && state.workspace.preferences.palette==='mineral'");
            assertEquals("true",js(scenario,"state.workspace.preferences.appearance_version===2 && state.workspace.notes[0].body==='Retain the exact original text'"));
        }
    }
}
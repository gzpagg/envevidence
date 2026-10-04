package io.github.gzpagg.envevidence;

import android.content.Context;
import android.net.Uri;
import android.webkit.WebResourceResponse;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.core.app.ActivityScenario;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import androidx.test.platform.app.InstrumentationRegistry;
import org.json.*;
import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import org.junit.runner.RunWith;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LabMediaTest {
    private JSONObject originalState;
    private String originalPending,originalLastStop;
    private final Set<String> createdIds=new HashSet<>();
    private final List<File> createdArchives=new ArrayList<>();
    @Before public void rememberWorkspace() throws Exception {originalState=LabStore.load(context());originalPending=context().getSharedPreferences("lab-audio",0).getString("pending",null);originalLastStop=context().getSharedPreferences("lab-audio",0).getString("last_stop",null);context().getSharedPreferences("lab-audio",0).edit().clear().commit();}
    @After public void restoreWorkspace() throws Exception {
        synchronized(LabStore.LOCK){if(originalState==null)LabStore.file(context()).delete();else LabStore.save(context(),originalState);}
        android.content.SharedPreferences.Editor prefs=context().getSharedPreferences("lab-audio",0).edit().clear();if(originalPending!=null)prefs.putString("pending",originalPending);if(originalLastStop!=null)prefs.putString("last_stop",originalLastStop);prefs.commit();
        for(String id:createdIds){LabAudio.file(context(),id+".m4a").delete();for(String suffix:new String[]{".jpg",".png",".webp",".thumb.jpg"})LabPhotos.file(context(),id+suffix).delete();}
        for(File f:createdArchives)f.delete();
    }
    private Context context(){return InstrumentationRegistry.getInstrumentation().getTargetContext();}
    private String id(){String value=UUID.randomUUID().toString().replace("-","");createdIds.add(value);return value;}
    private JSONObject fixture(String experiment,String record,String audioId,byte[] bytes) throws Exception {
        JSONObject clock=LabStore.clock(context());JSONObject state=new JSONObject().put("format","envevidence-android").put("schema_version",1).put("projects",new JSONArray()).put("workspace",new JSONObject().put("schema_version",1).put("preferences",new JSONObject("{\"language\":\"en\",\"palette\":\"clay\",\"accent\":\"#A65338\",\"background\":\"#F7F5F0\",\"order\":[\"evidence\",\"learning\",\"tasks\",\"notes\"],\"hidden\":[]}")).put("goals",new JSONArray()).put("tasks",new JSONArray()).put("notes",new JSONArray()));
        JSONObject lab=new JSONObject().put("version",2).put("demo_loaded",false);for(String key:new String[]{"experiments","timers","counters","records","events","samples","workflows","experiment_templates","observation_phrases"})lab.put(key,new JSONArray());state.put("lab",lab);
        lab.getJSONArray("experiments").put(new JSONObject().put("id",experiment).put("title","Synthetic media test").put("description","").put("sample","").put("archived",false).put("run",JSONObject.NULL).put("water",JSONObject.NULL).put("started",clock).put("ended",JSONObject.NULL));
        JSONObject r=new JSONObject().put("id",record).put("experiment_id",experiment).put("body","Synthetic observation").put("sample","").put("at",clock).put("elapsed_ms",0).put("archived",false).put("photos",new JSONArray()).put("revisions",new JSONArray()).put("audios",new JSONArray());lab.getJSONArray("records").put(r);
        if(audioId!=null)r.getJSONArray("audios").put(new JSONObject().put("id",audioId).put("name","Synthetic.m4a").put("ext","m4a").put("mime","audio/mp4").put("bytes",bytes.length).put("duration_ms",1234).put("sha256",LabAudio.sha256(new ByteArrayInputStream(bytes))).put("recorded_at",clock).put("elapsed_ms",0));
        return state;
    }
    private File archive(String name) {File result=new File(context().getCacheDir(),name+"-"+id()+".zip");createdArchives.add(result);return result;}
    private void zip(File f,Map<String,byte[]> files) throws Exception {try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(f))){for(Map.Entry<String,byte[]> e:files.entrySet()){z.putNextEntry(new ZipEntry(e.getKey()));z.write(e.getValue());z.closeEntry();}}}
    @Test public void audioAndWorkflowSnapshotsRoundTripWithChecksums() throws Exception {
        Context c=context();String exp=id(),rec=id(),audio=id();byte[] bytes="Synthetic media bytes for archive integrity, not playable audio".getBytes(StandardCharsets.UTF_8);File original=LabAudio.file(c,audio+".m4a");LabPhotos.write(original,bytes);JSONObject state=fixture(exp,rec,audio,bytes);JSONObject lab=state.getJSONObject("lab");
        JSONObject clock=LabStore.clock(c);String templateId=id(),otherTemplateId=id(),otherExperiment=id();
        JSONObject selectedTemplate=new JSONObject().put("id",templateId).put("title","Selected experiment template").put("description","Selected conditions").put("run",JSONObject.NULL).put("water",JSONObject.NULL).put("planned_minutes",new JSONArray()).put("timer_presets",new JSONArray()).put("steps",new JSONArray()).put("version",1).put("created",clock).put("updated",clock).put("archived",false);
        JSONObject unrelatedTemplate=new JSONObject(selectedTemplate.toString()).put("id",otherTemplateId).put("title","Private unrelated experiment template").put("description","Private unrelated conditions");
        lab.getJSONArray("experiment_templates").put(selectedTemplate).put(unrelatedTemplate);
        JSONObject selectedFlow=new JSONObject().put("id",id()).put("experiment_id",exp).put("template_id",templateId).put("template_version",1).put("template_snapshot",new JSONObject(selectedTemplate.toString())).put("created",clock).put("ended",JSONObject.NULL).put("steps",new JSONArray());lab.getJSONArray("workflows").put(selectedFlow);
        lab.getJSONArray("experiments").put(new JSONObject(lab.getJSONArray("experiments").getJSONObject(0).toString()).put("id",otherExperiment));lab.getJSONArray("workflows").put(new JSONObject(selectedFlow.toString()).put("id",id()).put("experiment_id",otherExperiment).put("template_id",otherTemplateId).put("template_snapshot",new JSONObject(unrelatedTemplate.toString())));
        lab.getJSONArray("observation_phrases").put(new JSONObject().put("id",id()).put("text","Private global phrase").put("created",clock).put("updated",clock));LabStore.save(c,state);File all=archive("audio-full");LabPhotos.backup(c,Uri.fromFile(all));
        try(ZipFile z=new ZipFile(all)){assertArrayEquals(bytes,z.getInputStream(z.getEntry("audio/"+audio+".m4a")).readAllBytes());JSONObject manifest=new JSONObject(new String(z.getInputStream(z.getEntry("media-manifest.json")).readAllBytes(),StandardCharsets.UTF_8));assertEquals(LabAudio.sha256(original),manifest.getJSONObject("files").getJSONObject("audio/"+audio+".m4a").getString("sha256"));}
        JSONObject restored=LabPhotos.restore(c,Uri.fromFile(all));assertEquals(audio,restored.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").getJSONObject(0).getString("id"));File single=archive("audio-single");LabPhotos.backup(c,Uri.fromFile(single),exp);JSONObject partial=LabPhotos.restore(c,Uri.fromFile(single));assertEquals(1,partial.getJSONObject("lab").getJSONArray("workflows").length());assertEquals(1,partial.getJSONObject("lab").getJSONArray("experiment_templates").length());assertEquals(templateId,partial.getJSONObject("lab").getJSONArray("experiment_templates").getJSONObject(0).getString("id"));assertEquals(0,partial.getJSONObject("lab").getJSONArray("observation_phrases").length());assertEquals(1,partial.getJSONObject("lab").getJSONArray("experiments").length());assertFalse(partial.toString().contains("Private unrelated"));assertFalse(partial.toString().contains("Private global phrase"));assertEquals(2,restored.getJSONObject("lab").getJSONArray("experiment_templates").length());assertEquals(1,restored.getJSONObject("lab").getJSONArray("observation_phrases").length());
        lab.put("experiment_templates",new JSONArray().put(unrelatedTemplate));LabStore.save(c,state);LabPhotos.backup(c,Uri.fromFile(single),exp);JSONObject snapshotOnly=LabPhotos.restore(c,Uri.fromFile(single));assertEquals(0,snapshotOnly.getJSONObject("lab").getJSONArray("experiment_templates").length());assertEquals("Selected experiment template",snapshotOnly.getJSONObject("lab").getJSONArray("workflows").getJSONObject(0).getJSONObject("template_snapshot").getString("title"));original.delete();all.delete();single.delete();
    }
    @Test public void failedRestoreLeavesExistingWorkspaceAndNewMediaUntouched() throws Exception {
        Context c=context();String exp=id(),rec=id(),audio=id();byte[] good="first staged file".getBytes(StandardCharsets.UTF_8);JSONObject state=fixture(exp,rec,audio,good);LabStore.save(c,state);String before=LabStore.load(c).toString();File backup=archive("bad-path");Map<String,byte[]> entries=new LinkedHashMap<>();entries.put("workspace.json",state.toString().getBytes(StandardCharsets.UTF_8));entries.put("audio/"+audio+".m4a",good);entries.put("audio/../escaped.m4a",good);zip(backup,entries);
        try{LabPhotos.restore(c,Uri.fromFile(backup));fail("Unsafe path must reject restore");}catch(IOException e){assertEquals("invalid",e.getMessage());}assertEquals(before,LabStore.load(c).toString());assertFalse(LabAudio.file(c,audio+".m4a").exists());
        entries.remove("audio/../escaped.m4a");entries.put("audio/"+audio+".m4a","different contents".getBytes(StandardCharsets.UTF_8));zip(backup,entries);try{LabPhotos.restore(c,Uri.fromFile(backup));fail("Metadata hash mismatch must reject restore");}catch(IOException e){assertEquals("mediaChecksum",e.getMessage());}assertFalse(LabAudio.file(c,audio+".m4a").exists());assertEquals(before,LabStore.load(c).toString());
        entries.put("audio/"+audio+".m4a",good);zip(backup,entries);byte[] local="pre-existing conflicting audio".getBytes(StandardCharsets.UTF_8);LabPhotos.write(LabAudio.file(c,audio+".m4a"),local);
        try{LabPhotos.restore(c,Uri.fromFile(backup));fail("Different existing bytes must reject restore");}catch(IOException e){assertEquals("audioConflict",e.getMessage());}assertArrayEquals(local,LabStore.read(new FileInputStream(LabAudio.file(c,audio+".m4a")),LabStore.LIMIT));assertEquals(before,LabStore.load(c).toString());backup.delete();
    }
    @Test public void audioPathAndPartialResponsesAreBounded() throws Exception {
        Context c=context();String audio=id();byte[] bytes={0,1,2,3,4,5,6,7,8,9};File f=LabAudio.file(c,audio+".m4a");LabPhotos.write(f,bytes);WebResourceResponse r=LabAudio.response(c,audio+".m4a","bytes=2-5","GET");assertEquals(206,r.getStatusCode());assertEquals("audio/mp4",r.getMimeType());assertEquals("bytes 2-5/10",r.getResponseHeaders().get("Content-Range"));try(InputStream in=r.getData()){assertArrayEquals(new byte[]{2,3,4,5},in.readAllBytes());}
        assertEquals(416,LabAudio.response(c,audio+".m4a","bytes=10-","GET").getStatusCode());assertEquals(404,LabAudio.response(c,"../"+audio+".m4a",null,"GET").getStatusCode());assertEquals(405,LabAudio.response(c,audio+".m4a",null,"POST").getStatusCode());WebResourceResponse head=LabAudio.response(c,audio+".m4a",null,"HEAD");assertEquals(200,head.getStatusCode());assertEquals(0,head.getData().readAllBytes().length);assertEquals("10",head.getResponseHeaders().get("Content-Length"));f.delete();
    }
    @Test public void oldPhotoOnlyZipStillRestores() throws Exception {
        Context c=context();String exp=id(),rec=id();JSONObject state=fixture(exp,rec,null,new byte[0]);String photo=id();android.graphics.Bitmap b=android.graphics.Bitmap.createBitmap(8,8,android.graphics.Bitmap.Config.ARGB_8888);ByteArrayOutputStream out=new ByteArrayOutputStream();b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);b.recycle();JSONObject meta=LabPhotos.ingest(c,out.toByteArray(),"Synthetic.png",photo);meta.remove("sha256");state.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("photos").put(meta);Map<String,byte[]> entries=new LinkedHashMap<>();entries.put("workspace.json",state.toString().getBytes(StandardCharsets.UTF_8));entries.put("photos/"+photo+".png",out.toByteArray());entries.put("photos/"+photo+".thumb.jpg",LabStore.read(new FileInputStream(LabPhotos.file(c,photo+".thumb.jpg")),LabStore.LIMIT));File old=archive("legacy-photo");zip(old,entries);assertEquals(photo,LabPhotos.restore(c,Uri.fromFile(old)).getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("photos").getJSONObject(0).getString("id"));LabPhotos.file(c,photo+".png").delete();LabPhotos.file(c,photo+".thumb.jpg").delete();old.delete();
    }
    private LabAudio recorder(MainActivity a) throws Exception {java.lang.reflect.Field field=MainActivity.class.getDeclaredField("audio");field.setAccessible(true);return (LabAudio)field.get(a);}
    private String js(ActivityScenario<MainActivity> scenario,String script) throws Exception {CountDownLatch done=new CountDownLatch(1);AtomicReference<String> value=new AtomicReference<>();scenario.onActivity(a->{android.view.ViewGroup root=a.findViewById(android.R.id.content);android.webkit.WebView web=(android.webkit.WebView)((android.view.ViewGroup)root.getChildAt(0)).getChildAt(0);web.evaluateJavascript(script,v->{value.set(v);done.countDown();});});assertTrue(done.await(10,TimeUnit.SECONDS));return value.get();}
    @Test public void leavingAndRecreatingActivitySavesCorrectObservationAndPlayableAudio() throws Exception {
        Context c=context();android.os.ParcelFileDescriptor pipe=InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand("pm grant io.github.gzpagg.envevidence android.permission.RECORD_AUDIO");try(InputStream in=new android.os.ParcelFileDescriptor.AutoCloseInputStream(pipe)){in.readAllBytes();}
        String experiment=id(),record=id(),other=id();JSONObject state=fixture(experiment,record,null,new byte[0]);JSONObject alternate=new JSONObject(state.getJSONObject("lab").getJSONArray("records").getJSONObject(0).toString()).put("id",other);state.getJSONObject("lab").getJSONArray("records").put(alternate);LabStore.save(c,state);AtomicReference<Throwable> failure=new AtomicReference<>();
        try(ActivityScenario<MainActivity> scenario=ActivityScenario.launch(MainActivity.class)){
            scenario.onActivity(a->{try{assertTrue(recorder(a).start(record).getBoolean("active"));}catch(Throwable e){failure.set(e);}});if(failure.get()!=null)throw new AssertionError(failure.get());Thread.sleep(1400);
            scenario.moveToState(androidx.lifecycle.Lifecycle.State.CREATED);
            JSONObject saved=LabStore.load(c);JSONArray records=saved.getJSONObject("lab").getJSONArray("records");JSONObject audio=records.getJSONObject(0).getJSONArray("audios").getJSONObject(0);assertTrue(audio.getLong("duration_ms")>0);assertEquals(64,audio.getString("sha256").length());assertEquals(0,records.getJSONObject(1).getJSONArray("audios").length());createdIds.add(audio.getString("id"));File original=LabAudio.file(c,audio.getString("id")+".m4a");assertEquals(audio.getString("sha256"),LabAudio.sha256(original));assertTrue(LabAudio.mediaDuration(original)>0);
            JSONObject audit=null;for(int i=0;i<saved.getJSONObject("lab").getJSONArray("events").length();i++){JSONObject candidate=saved.getJSONObject("lab").getJSONArray("events").getJSONObject(i);if("audio_added".equals(candidate.optString("kind")))audit=candidate;}assertNotNull(audit);assertEquals(record,audit.getString("record_id"));assertEquals(audio.getString("id"),audit.getString("audio_id"));
            LabStore.save(c,new JSONObject(state.toString()));JSONObject afterStaleSave=LabStore.load(c);assertEquals(1,afterStaleSave.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").length());assertEquals(1,afterStaleSave.getJSONObject("lab").getJSONArray("events").length());assertEquals(audit.getString("id"),afterStaleSave.getJSONObject("lab").getJSONArray("events").getJSONObject(0).getString("id"));
            scenario.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED);scenario.recreate();scenario.onActivity(a->{try{assertFalse(recorder(a).status().getBoolean("active"));assertEquals("background",recorder(a).status().getJSONObject("last_stop").getString("reason"));}catch(Throwable e){failure.set(e);}});if(failure.get()!=null)throw new AssertionError(failure.get());
            assertEquals(audio.getString("id"),LabStore.load(c).getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").getJSONObject(0).getString("id"));
            boolean uiReady=false;for(int i=0;i<100;i++){if("true".equals(js(scenario,"typeof bridge==='function' && typeof state==='object' && !!state.lab && document.readyState==='complete'"))){uiReady=true;break;}Thread.sleep(100);}assertTrue("App ready after recreation",uiReady);
            // Exercise the actual WebView asset route and CSP with a real finalized M4A.
            js(scenario,"(()=>{window.nativePlayback=document.createElement('audio');nativePlayback.src='https://appassets.androidplatform.net/audio/"+audio.getString("id")+".m4a';document.body.append(nativePlayback);nativePlayback.load();return true;})()");
            boolean loaded=false;for(int i=0;i<60;i++){if("true".equals(js(scenario,"window.nativePlayback && nativePlayback.readyState>=1 && nativePlayback.duration>0"))){loaded=true;break;}Thread.sleep(100);}assertTrue("WebView recognizes private M4A metadata",loaded);assertEquals("true",js(scenario,"(()=>{nativePlayback.currentTime=0.3;return !nativePlayback.error;})()"));original.delete();
        }
    }

}

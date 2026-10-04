package io.github.gzpagg.envevidence;

import android.content.Context;
import android.media.MediaMetadataRetriever;
import android.media.MediaRecorder;
import android.os.Build;
import android.os.SystemClock;
import android.webkit.WebResourceResponse;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;

/** Private AAC observations. A small journal recovers finalized files after process loss. */
final class LabAudio {
    static final int MAX_BYTES = 30 * 1024 * 1024;
    static final int MAX_DURATION_MS = 30 * 60 * 1000;
    private static final String PREFS = "lab-audio";
    interface Listener { void stopped(JSONObject notice, JSONObject state); }
    private final Context context;
    private final Listener listener;
    private MediaRecorder recorder;
    private JSONObject pending;
    private long startedMono;

    LabAudio(Context context, Listener listener) { this.context=context.getApplicationContext(); this.listener=listener; }
    static File dir(Context c) throws IOException { File d=new File(c.getFilesDir(),"audio"); if(!d.exists()&&!d.mkdirs())throw new IOException("audioFailed"); return d; }
    static File file(Context c,String name) throws IOException { if(name==null||!name.matches("[a-f0-9]{32}\\.m4a"))throw new IOException("invalid"); return new File(dir(c),name); }
    static String sha256(File f) throws Exception { try(InputStream in=new FileInputStream(f)){return sha256(in);} }
    static String sha256(InputStream in) throws Exception { MessageDigest hash=MessageDigest.getInstance("SHA-256");byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)hash.update(b,0,n);StringBuilder out=new StringBuilder();for(byte v:hash.digest())out.append(String.format(Locale.ROOT,"%02x",v&255));return out.toString(); }
    static long mediaDuration(File f) throws Exception { MediaMetadataRetriever r=new MediaMetadataRetriever();try{r.setDataSource(f.getAbsolutePath());String mime=r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_MIMETYPE);String duration=r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);if(mime==null||!mime.startsWith("audio/")&&!mime.equals("video/mp4")||duration==null)throw new IOException("audioFailed");long ms=Long.parseLong(duration);if(ms<=0||ms>MAX_DURATION_MS+2000)throw new IOException("audioFailed");return ms;}finally{r.release();} }
    static JSONObject record(Context c,String recordId) throws Exception { JSONObject state=LabStore.load(c);if(state==null||state.optJSONObject("lab")==null)throw new IOException("invalid");JSONArray records=state.getJSONObject("lab").getJSONArray("records");for(int i=0;i<records.length();i++){JSONObject r=records.getJSONObject(i);if(recordId.equals(r.optString("id")))return r;}throw new IOException("invalid"); }
    synchronized JSONObject start(String recordId) throws Exception {
        if(recorder!=null)throw new IOException("audioBusy");
        recover();
        if(context.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=android.content.pm.PackageManager.PERMISSION_GRANTED)throw new IOException("micDenied");
        if(recordId==null||!recordId.matches("[a-f0-9]{32}"))throw new IOException("invalid");
        synchronized(LabStore.LOCK){record(context,recordId);}
        String id=UUID.randomUUID().toString().replace("-","");File output=file(context,id+".m4a");
        JSONObject journal=new JSONObject().put("recordId",recordId).put("audioId",id).put("started",LabStore.clock(context));
        MediaRecorder next=Build.VERSION.SDK_INT>=31?new MediaRecorder(context):new MediaRecorder();
        try {
            next.setAudioSource(MediaRecorder.AudioSource.MIC);next.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);next.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            next.setAudioChannels(1);next.setAudioSamplingRate(44100);next.setAudioEncodingBitRate(64000);next.setMaxDuration(MAX_DURATION_MS);next.setMaxFileSize(MAX_BYTES);
            next.setOutputFile(output.getAbsolutePath());
            next.setOnInfoListener((m,what,extra)->{if(what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED||what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED)automatic(m,what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED?"durationLimit":"sizeLimit");});
            next.setOnErrorListener((m,what,extra)->automatic(m,"recorderError"));
            if(!context.getSharedPreferences(PREFS,0).edit().putString("pending",journal.toString()).remove("last_stop").commit())throw new IOException("audioFailed");
            next.prepare();next.start();recorder=next;pending=journal;startedMono=SystemClock.elapsedRealtime();return status();
        }catch(Exception e){try{next.release();}catch(Exception ignored){}output.delete();context.getSharedPreferences(PREFS,0).edit().remove("pending").commit();throw new IOException("audioFailed",e);}
    }
    synchronized JSONObject status() throws Exception { JSONObject out=new JSONObject().put("active",recorder!=null).put("recordId",pending==null?JSONObject.NULL:pending.getString("recordId")).put("audioId",pending==null?JSONObject.NULL:pending.getString("audioId")).put("duration_ms",recorder==null?0:Math.max(0,SystemClock.elapsedRealtime()-startedMono)).put("max_duration_ms",MAX_DURATION_MS).put("max_bytes",MAX_BYTES);String last=context.getSharedPreferences(PREFS,0).getString("last_stop",null);return out.put("last_stop",last==null?JSONObject.NULL:new JSONObject(last)); }
    synchronized boolean active(){return recorder!=null;}
    private JSONObject finalized(JSONObject journal,File f) throws Exception {
        if(!f.isFile()||f.length()==0)throw new IOException("audioTooShort");
        if(f.length()>MAX_BYTES)throw new IOException("tooLarge");
        return new JSONObject().put("id",journal.getString("audioId")).put("name","Observation.m4a")
            .put("ext","m4a").put("mime","audio/mp4").put("bytes",f.length())
            .put("duration_ms",mediaDuration(f)).put("sha256",sha256(f)).put("recorded_at",journal.getJSONObject("started"));
    }
    private void failedCommit(JSONObject journal,String reason,String code) throws Exception {
        // Keep both the file and journal for the next explicit load/recovery attempt.
        JSONObject n=new JSONObject().put("id",UUID.randomUUID().toString()).put("reason",reason)
            .put("recordId",journal.getString("recordId")).put("audioId",journal.getString("audioId")).put("error",code);
        context.getSharedPreferences(PREFS,0).edit().putString("last_stop",n.toString()).commit();
    }
    synchronized JSONObject stop(String reason) throws Exception {
        if(recorder==null)throw new IOException("audioNotRecording");
        MediaRecorder old=recorder;JSONObject journal=pending;recorder=null;pending=null;
        boolean tooShort=false;
        try{old.stop();}catch(RuntimeException e){tooShort=true;}finally{old.release();}
        File f=file(context,journal.getString("audioId")+".m4a");JSONObject metadata;
        try{if(tooShort)throw new IOException("audioTooShort");metadata=finalized(journal,f);}
        catch(Exception e){f.delete();String code="audioTooShort".equals(e.getMessage())?"audioTooShort":"audioFailed";notice(journal,reason,code);throw new IOException(code,e);}
        try{JSONObject state=attach(context,journal.getString("recordId"),metadata);notice(journal,reason,null);return state;}
        catch(Exception e){String code="audioConflict".equals(e.getMessage())?"audioConflict":"audioSaveFailed";failedCommit(journal,reason,code);throw new IOException(code,e);}
    }
    synchronized void cancel() throws Exception { if(recorder==null)throw new IOException("audioNotRecording");MediaRecorder old=recorder;JSONObject journal=pending;recorder=null;pending=null;try{old.stop();}catch(RuntimeException ignored){}finally{old.release();}file(context,journal.getString("audioId")+".m4a").delete();context.getSharedPreferences(PREFS,0).edit().remove("pending").remove("last_stop").commit(); }
    private void notice(JSONObject journal,String reason,String error) throws Exception { JSONObject n=new JSONObject().put("id",UUID.randomUUID().toString()).put("reason",reason).put("recordId",journal.getString("recordId")).put("audioId",journal.getString("audioId"));if(error!=null)n.put("error",error);context.getSharedPreferences(PREFS,0).edit().remove("pending").putString("last_stop",n.toString()).commit(); }
    private synchronized void automatic(MediaRecorder source,String reason){if(recorder==null||recorder!=source)return;JSONObject state=null;try{state=stop(reason);}catch(Exception ignored){}try{JSONObject n=status().optJSONObject("last_stop");if(n!=null)listener.stopped(n,state);}catch(Exception ignored){} }
    synchronized void stopForBackground(){if(recorder!=null)automatic(recorder,"background");}
    synchronized void recover() throws Exception {
        if(recorder!=null)return;
        String raw=context.getSharedPreferences(PREFS,0).getString("pending",null);if(raw==null)return;
        JSONObject journal=new JSONObject(raw);File f=file(context,journal.getString("audioId")+".m4a");JSONObject metadata;
        try{metadata=finalized(journal,f);}
        catch(Exception e){f.delete();notice(journal,"interrupted","audioFailed");return;}
        try{attach(context,journal.getString("recordId"),metadata);notice(journal,"interrupted",null);}
        catch(Exception e){String code="audioConflict".equals(e.getMessage())?"audioConflict":"audioSaveFailed";failedCommit(journal,"interrupted",code);throw new IOException(code,e);}
    }
    static JSONObject attach(Context c,String recordId,JSONObject audio) throws Exception { synchronized(LabStore.LOCK){JSONObject state=LabStore.load(c);if(state==null)throw new IOException("invalid");JSONObject lab=state.getJSONObject("lab");JSONArray records=lab.getJSONArray("records");for(int i=0;i<records.length();i++){JSONObject r=records.getJSONObject(i);if(!recordId.equals(r.optString("id")))continue;JSONArray audios=r.optJSONArray("audios");if(audios==null){audios=new JSONArray();r.put("audios",audios);}for(int j=0;j<audios.length();j++)if(audio.getString("id").equals(audios.getJSONObject(j).getString("id"))){JSONObject previous=audios.getJSONObject(j);if(!audio.optString("sha256").equals(previous.optString("sha256"))||audio.optLong("bytes")!=previous.optLong("bytes"))throw new IOException("audioConflict");return state;}
        JSONObject recorded=audio.optJSONObject("recorded_at");if(recorded==null)recorded=LabStore.clock(c);audio.put("recorded_at",recorded);long elapsed=0;JSONArray experiments=lab.getJSONArray("experiments");for(int k=0;k<experiments.length();k++){JSONObject e=experiments.getJSONObject(k);if(e.getString("id").equals(r.optString("experiment_id"))){JSONObject until=e.optJSONObject("ended");elapsed=LabStore.elapsed(new JSONObject().put("status","running").put("anchor",e.getJSONObject("started")),until==null?recorded:until);break;}}audio.put("elapsed_ms",elapsed);audios.put(audio);lab.getJSONArray("events").put(new JSONObject().put("id",UUID.randomUUID().toString().replace("-","")).put("experiment_id",r.opt("experiment_id")).put("kind","audio_added").put("record_id",recordId).put("audio_id",audio.getString("id")).put("label",audio.getString("name")).put("at",recorded).put("elapsed_ms",elapsed));LabStore.save(c,state);return state;}throw new IOException("invalid");} }

    static final class ByteRange { final long start,end;ByteRange(long start,long end){this.start=start;this.end=end;}long length(){return end-start+1;} }
    static ByteRange range(String value,long length) throws IOException { if(length<=0)throw new IOException("range");if(value==null||value.isEmpty())return new ByteRange(0,length-1);if(!value.matches("bytes=([0-9]+-[0-9]*|-[0-9]+)"))throw new IOException("range");String[] parts=value.substring(6).split("-",-1);try{long start,end;if(parts[0].isEmpty()){long suffix=Long.parseLong(parts[1]);if(suffix<=0)throw new IOException("range");start=Math.max(0,length-suffix);end=length-1;}else{start=Long.parseLong(parts[0]);end=parts[1].isEmpty()?length-1:Math.min(length-1,Long.parseLong(parts[1]));if(start>=length||start>end)throw new IOException("range");}return new ByteRange(start,end);}catch(NumberFormatException e){throw new IOException("range",e);} }
    static WebResourceResponse response(Context c,String name,String range,String method) { try{if(!"GET".equals(method)&&!"HEAD".equals(method))return denied(405,"Method Not Allowed");File f=file(c,name);if(!f.isFile()||f.length()==0||f.length()>MAX_BYTES)return denied(404,"Not Found");long length=f.length();ByteRange bytes;try{bytes=range(range,length);}catch(IOException e){Map<String,String> h=new HashMap<>();h.put("Content-Range","bytes */"+length);h.put("Accept-Ranges","bytes");h.put("Content-Length","0");return new WebResourceResponse("audio/mp4",null,416,"Range Not Satisfiable",h,new ByteArrayInputStream(new byte[0]));}Map<String,String> h=new HashMap<>();h.put("Accept-Ranges","bytes");h.put("Content-Length",Long.toString(bytes.length()));h.put("Cache-Control","no-store");h.put("X-Content-Type-Options","nosniff");boolean partial=range!=null&&!range.isEmpty();if(partial)h.put("Content-Range","bytes "+bytes.start+"-"+bytes.end+"/"+length);InputStream stream=new ByteArrayInputStream(new byte[0]);if(!"HEAD".equals(method)){RandomAccessFile in=new RandomAccessFile(f,"r");in.seek(bytes.start);stream=new InputStream(){long left=bytes.length();public int read() throws IOException{if(left<=0)return -1;int v=in.read();if(v!=-1)left--;return v;}public int read(byte[] b,int off,int len)throws IOException{if(len==0)return 0;if(left<=0)return -1;int n=in.read(b,off,(int)Math.min(left,len));if(n>0)left-=n;return n;}public void close()throws IOException{in.close();}};}return new WebResourceResponse("audio/mp4",null,partial?206:200,partial?"Partial Content":"OK",h,stream);}catch(Exception e){return denied(404,"Not Found");} }
    private static WebResourceResponse denied(int code,String reason){return new WebResourceResponse("text/plain","UTF-8",code,reason,Collections.singletonMap("Content-Length","0"),new ByteArrayInputStream(new byte[0]));}
}

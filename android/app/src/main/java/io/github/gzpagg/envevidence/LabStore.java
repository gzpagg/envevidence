package io.github.gzpagg.envevidence;

import android.content.Context;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.AtomicFile;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

final class LabStore {
    static final Object LOCK = new Object();
    static final int LIMIT = 30 * 1024 * 1024;
    static JSONObject clock(Context c) throws Exception {
        android.content.SharedPreferences prefs=c.getSharedPreferences("lab-clock",0);
        String instance=prefs.getString("instance",null);if(instance==null){instance=java.util.UUID.randomUUID().toString();prefs.edit().putString("instance",instance).commit();}
        return new JSONObject().put("wall",System.currentTimeMillis()).put("mono",SystemClock.elapsedRealtime())
            .put("boot",instance+":"+Settings.Global.getInt(c.getContentResolver(),Settings.Global.BOOT_COUNT,0));
    }
    static long elapsed(JSONObject timer, JSONObject now) {
        if("staged".equals(timer.optString("kind")))try{return phase(timer,now).elapsed;}catch(Exception ignored){return 0;}
        return rawElapsed(timer,now);
    }
    static long difference(JSONObject a,JSONObject b){return Math.max(0,a.optString("boot").equals(b.optString("boot"))?b.optLong("mono")-a.optLong("mono"):b.optLong("wall")-a.optLong("wall"));}
    static long rawElapsed(JSONObject timer, JSONObject now) {
        long value=timer.optLong("elapsed_ms");
        JSONObject anchor=timer.optJSONObject("anchor");
        if("running".equals(timer.optString("status"))&&anchor!=null)
            value+=Math.max(0,anchor.optString("boot").equals(now.optString("boot"))?now.optLong("mono")-anchor.optLong("mono"):now.optLong("wall")-anchor.optLong("wall"));
        return value;
    }
    /** Derived state matches Lab.timerState: pauses and manual waits never shift future stages. */
    static final class Phase {long elapsed,raw,next=-1,remaining,duration,boundary,totalSteps,completed,stage,repeat,start;String kind="stage";}
    static Phase phase(JSONObject t,JSONObject now)throws Exception{
        JSONArray stages=t.getJSONArray("stages");long repeats=t.getLong("repeat_count"),delay=t.getLong("delay_ms"),total=t.getLong("duration_ms"),round=0;
        if(stages.length()==0||repeats<1||delay<0||total<1||total>9007199254740991L)throw new IOException("invalid");
        for(int i=0;i<stages.length();i++){long d=stages.getJSONObject(i).getLong("duration_ms");if(d<1)throw new IOException("invalid");round=Math.addExact(round,d);}
        if(Math.addExact(Math.multiplyExact(round,repeats),delay)!=total)throw new IOException("invalid");
        Phase p=new Phase();p.raw=rawElapsed(t,now);p.elapsed=Math.min(total,p.raw);p.totalSteps=Math.multiplyExact(stages.length(),repeats);p.completed=t.optLong("completed_steps");p.stage=p.completed%stages.length();p.repeat=Math.min(repeats-1,p.completed/stages.length());long end=delay;
        boolean auto="auto".equals(t.optString("transition_mode"));
        if(p.elapsed<delay){p.kind="delay";p.completed=0;p.stage=0;p.repeat=0;p.duration=delay;}
        else if(auto){long active=p.elapsed-delay,within; p.repeat=Math.min(repeats-1,active/round);within=active-p.repeat*round;p.start=delay+p.repeat*round;p.completed=p.repeat*stages.length();long cumulative=0;
            for(int i=0;i<stages.length();i++){p.duration=stages.getJSONObject(i).getLong("duration_ms");end=p.start+p.duration;cumulative+=p.duration;if(within<cumulative){p.stage=i;break;}p.completed++;p.start=end;p.stage=Math.min(i+1,stages.length()-1);}
            if(p.elapsed>=total){p.kind="done";p.completed=p.totalSteps;p.stage=stages.length()-1;p.repeat=repeats-1;p.duration=stages.getJSONObject((int)p.stage).getLong("duration_ms");p.start=total-p.duration;end=total;}
        }else{p.start=delay+(p.completed/stages.length())*round;for(int i=0;i<p.stage;i++)p.start+=stages.getJSONObject(i).getLong("duration_ms");p.duration=stages.getJSONObject((int)p.stage).getLong("duration_ms");end=p.start+(p.completed<p.totalSteps?p.duration:0);
            if(p.completed>=p.totalSteps){p.kind="done";p.elapsed=total;end=total;p.stage=stages.length()-1;}
            else if(p.elapsed>=end){p.elapsed=end;p.kind="waiting";}}
        if("done".equals(t.optString("status")))p.kind="done";
        p.boundary="delay".equals(p.kind)?0:(delay>0?1:0)+p.completed+(!auto&&"waiting".equals(p.kind)?1:0);p.remaining=Math.max(0,end-p.elapsed);if(!"done".equals(p.kind)&&!"waiting".equals(p.kind))p.next=end;return p;
    }
    /** A historical boundary is not an alarm. Only a fresh crossing or a local pending reminder is. */
    static long alertBoundary(JSONObject t,Phase p){String status=t.optString("status");if(t.optBoolean("archived")||"idle".equals(status)||"paused".equals(status))return 0;long pending=Math.min(p.boundary,t.optLong("pending_boundary",0));return "running".equals(status)&&p.boundary>t.optLong("audit_cursor")?Math.max(pending,p.boundary):pending;}
    /** Imports and explicit acknowledgements advance the local delivery baseline before new crossings. */
    static long alertBaseline(JSONObject t,long sent){return t.optLong("pending_boundary",0)==0?Math.max(sent,t.optLong("audit_cursor")):sent;}
    static boolean reconcile(JSONObject state,JSONObject now)throws Exception{JSONObject lab=state.optJSONObject("lab");if(lab==null)return false;boolean changed=false;JSONArray timers=lab.getJSONArray("timers"),events=lab.getJSONArray("events"),experiments=lab.getJSONArray("experiments");
        for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);if(!"staged".equals(t.optString("kind"))||t.optBoolean("archived")||!"running".equals(t.optString("status")))continue;Phase p=phase(t,now);long previous=t.optLong("audit_cursor");
            if(p.boundary>previous){t.put("audit_cursor",p.boundary).put("pending_boundary",p.boundary);long scheduled="stage".equals(p.kind)?p.start:p.elapsed,late=Math.max(0,p.raw-scheduled);JSONObject at=new JSONObject().put("wall",Math.max(0,now.getLong("wall")-late)).put("mono",Math.max(0,now.getLong("mono")-late)).put("boot",now.getString("boot"));long expElapsed=0;
                for(int j=0;j<experiments.length();j++){JSONObject e=experiments.getJSONObject(j);if(e.optString("id").equals(t.optString("experiment_id"))){expElapsed=difference(e.getJSONObject("started"),e.optJSONObject("ended")==null?at:e.getJSONObject("ended"));break;}}
                events.put(new JSONObject().put("id",UUID.randomUUID().toString().replace("-","")).put("experiment_id",t.get("experiment_id")).put("kind","waiting".equals(p.kind)?"timer_stage_due":"done".equals(p.kind)?"timer_complete":"timer_progress").put("label",t.getString("title")).put("at",at).put("elapsed_ms",expElapsed).put("timer_id",t.getString("id")).put("cycle",t.optLong("cycle")).put("timer_elapsed_ms",scheduled).put("observed_elapsed_ms",p.elapsed).put("observed_at",new JSONObject(now.toString())).put("from_boundary",previous).put("to_boundary",p.boundary).put("boundary_count",p.boundary-previous).put("stage_index",p.stage).put("repeat_index",p.repeat));changed=true;}
            if("waiting".equals(p.kind)||"done".equals(p.kind)){t.put("elapsed_ms",p.elapsed).put("anchor",JSONObject.NULL).put("status","waiting".equals(p.kind)?"waiting":"done");changed=true;}}
        return changed;
    }
    static String boundaryKey(JSONObject e){String kind=e.optString("kind");return Arrays.asList("timer_progress","timer_stage_due","timer_complete").contains(kind)&&e.has("to_boundary")?e.optString("timer_id")+":"+e.optLong("cycle")+":"+e.optLong("to_boundary"):null;}
    /** Preserve native receiver audits and completed audio metadata when a WebView snapshot is older. */
    static void preserveNative(JSONObject state,JSONObject stored)throws Exception{if(stored==null||state.optJSONObject("lab")==null||stored.optJSONObject("lab")==null)return;JSONObject lab=state.getJSONObject("lab"),old=stored.getJSONObject("lab");Map<String,JSONObject> currentTimers=new HashMap<>(),currentRecords=new HashMap<>();
        JSONArray timers=lab.getJSONArray("timers"),records=lab.getJSONArray("records");for(int i=0;i<timers.length();i++)currentTimers.put(timers.getJSONObject(i).getString("id"),timers.getJSONObject(i));for(int i=0;i<records.length();i++)currentRecords.put(records.getJSONObject(i).getString("id"),records.getJSONObject(i));
        JSONArray previousTimers=old.getJSONArray("timers");for(int i=0;i<previousTimers.length();i++){JSONObject was=previousTimers.getJSONObject(i),t=currentTimers.get(was.optString("id"));if(t!=null&&"staged".equals(t.optString("kind"))&&t.optLong("cycle")==was.optLong("cycle")){long cursor=t.optLong("audit_cursor"),nativeCursor=was.optLong("audit_cursor");if("running".equals(t.optString("status"))&&nativeCursor>cursor)t.put("pending_boundary",Math.max(t.optLong("pending_boundary"),was.optLong("pending_boundary")));t.put("audit_cursor",Math.max(cursor,nativeCursor));}}
        JSONArray events=lab.getJSONArray("events"),previousEvents=old.getJSONArray("events");Set<String> ids=new HashSet<>(),boundaries=new HashSet<>();for(int i=0;i<events.length();i++){JSONObject e=events.getJSONObject(i);ids.add(e.optString("id"));String key=boundaryKey(e);if(key!=null)boundaries.add(key);}for(int i=0;i<previousEvents.length();i++){JSONObject e=previousEvents.getJSONObject(i);String key=boundaryKey(e);JSONObject t=currentTimers.get(e.optString("timer_id"));if(key!=null&&t!=null&&!ids.contains(e.optString("id"))&&!boundaries.contains(key)){events.put(e);ids.add(e.optString("id"));boundaries.add(key);}}
        JSONArray previousRecords=old.getJSONArray("records");for(int i=0;i<previousRecords.length();i++){JSONObject was=previousRecords.getJSONObject(i),r=currentRecords.get(was.optString("id"));if(r==null||was.optJSONArray("audios")==null)continue;JSONArray audios=r.optJSONArray("audios");if(audios==null){audios=new JSONArray();r.put("audios",audios);}Map<String,JSONObject> byId=new HashMap<>();for(int j=0;j<audios.length();j++)byId.put(audios.getJSONObject(j).getString("id"),audios.getJSONObject(j));for(int j=0;j<was.getJSONArray("audios").length();j++){JSONObject audio=was.getJSONArray("audios").getJSONObject(j),known=byId.get(audio.optString("id"));if(known==null){audios.put(audio);byId.put(audio.getString("id"),audio);}else if(!known.optString("sha256").equals(audio.optString("sha256")))throw new IOException("audioConflict");}}
        // Keep a native media audit only while its exact observation attachment is retained.
        for(int i=0;i<previousEvents.length();i++){
            JSONObject e=previousEvents.getJSONObject(i);String kind=e.optString("kind");
            if(!kind.equals("audio_added")&&!kind.equals("photo_added")||ids.contains(e.optString("id")))continue;
            JSONObject r=currentRecords.get(e.optString("record_id"));
            if(r==null||!Objects.equals(e.opt("experiment_id"),r.opt("experiment_id")))continue;
            JSONArray media=r.optJSONArray(kind.equals("audio_added")?"audios":"photos");
            String mediaId=e.optString(kind.equals("audio_added")?"audio_id":"photo_id");
            if(media==null||mediaId.isEmpty())continue;
            for(int j=0;j<media.length();j++)if(mediaId.equals(media.getJSONObject(j).optString("id"))){events.put(e);ids.add(e.optString("id"));break;}
        }
    }
    static AtomicFile file(Context c){return new AtomicFile(new File(c.getFilesDir(),"workspace.json"));}
    static byte[] read(InputStream source,int limit) throws Exception {
        if(source==null)throw new IOException("file");
        try(InputStream in=source;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>limit)throw new IOException("tooLarge");out.write(b,0,n);}return out.toByteArray();
        }
    }
    static JSONObject load(Context c) throws Exception {synchronized(LOCK){AtomicFile f=file(c);if(!f.getBaseFile().exists()&&!new File(f.getBaseFile()+".bak").exists())return null;return new JSONObject(new String(read(f.openRead(),LIMIT),StandardCharsets.UTF_8));}}
    static void save(Context c,JSONObject state) throws Exception {synchronized(LOCK){
        if(!"envevidence-android".equals(state.optString("format"))||state.optInt("schema_version")!=1)throw new IOException("invalid");
        preserveNative(state,load(c));reconcile(state,clock(c));
        byte[] data=state.toString().getBytes(StandardCharsets.UTF_8);if(data.length>LIMIT)throw new IOException("tooLarge");
        AtomicFile f=file(c);FileOutputStream out=null;try{out=f.startWrite();out.write(data);f.finishWrite(out);}catch(Exception e){if(out!=null)f.failWrite(out);throw new IOException("saveFailed",e);}
    }}
}

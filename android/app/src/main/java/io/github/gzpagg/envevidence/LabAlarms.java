package io.github.gzpagg.envevidence;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.Build;
import org.json.*;
import java.util.*;

/** One system alarm for the earliest due timer; timer count is not tied to the OS alarm cap. */
public class LabAlarms extends BroadcastReceiver {
    static final String CHANNEL="lab-timer-alerts", PREFS="lab-alerts";
    static boolean exact(Context c){return Build.VERSION.SDK_INT<31||c.getSystemService(AlarmManager.class).canScheduleExactAlarms();}
    static boolean notifications(Context c){NotificationManager manager=c.getSystemService(NotificationManager.class);NotificationChannel channel=manager.getNotificationChannel(CHANNEL);return manager.areNotificationsEnabled()&&(channel==null||channel.getImportance()!=NotificationManager.IMPORTANCE_NONE)&&(Build.VERSION.SDK_INT<33||c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED);}
    static void channel(Context c){NotificationChannel n=new NotificationChannel(CHANNEL,"Experiment timers / 实验计时",NotificationManager.IMPORTANCE_HIGH);n.setDescription("Countdown and sampling reminders / 倒计时与取样提醒");n.enableVibration(true);n.setSound(android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI,new android.media.AudioAttributes.Builder().setUsage(android.media.AudioAttributes.USAGE_ALARM).build());c.getSystemService(NotificationManager.class).createNotificationChannel(n);}
    static PendingIntent pending(Context c){return PendingIntent.getBroadcast(c,0,new Intent(c,LabAlarms.class).setAction("io.github.gzpagg.envevidence.TIMER"),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    static PendingIntent open(Context c){return PendingIntent.getActivity(c,1,new Intent(c,MainActivity.class).putExtra("openTimers",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    @android.annotation.SuppressLint("MissingPermission") // exact() checks the revocable special permission; races are caught.
    static void sync(Context c){try{synchronized(LabStore.LOCK){
        AlarmManager manager=c.getSystemService(AlarmManager.class);manager.cancel(pending(c));JSONObject s=LabStore.load(c);if(s==null||s.optJSONObject("lab")==null)return;
        JSONObject now=LabStore.clock(c);JSONArray timers=s.getJSONObject("lab").getJSONArray("timers");
        android.content.SharedPreferences prefs=c.getSharedPreferences(PREFS,0);android.content.SharedPreferences.Editor clean=prefs.edit();Set<String> delivered=new HashSet<>(prefs.getStringSet("delivered",Collections.emptySet())),valid=new HashSet<>(),stageKeys=new HashSet<>();long next=Long.MAX_VALUE;
        for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);String key=t.getString("id")+":"+t.optLong("cycle");valid.add(key);if("staged".equals(t.optString("kind"))){String stageKey="stage-"+key;stageKeys.add(stageKey);long sent=LabStore.alertBaseline(t,prefs.getLong(stageKey,0));clean.putLong(stageKey,sent);if(t.optBoolean("archived")||"idle".equals(t.optString("status"))||"paused".equals(t.optString("status")))continue;LabStore.Phase p=LabStore.phase(t,now);if(LabStore.alertBoundary(t,p)>sent)next=Math.min(next,50);else if("running".equals(t.optString("status"))&&p.next>=0)next=Math.min(next,Math.max(50,p.next-p.elapsed));continue;}if(t.optBoolean("archived")||!"running".equals(t.optString("status"))||!"countdown".equals(t.optString("kind"))||delivered.contains(key))continue;next=Math.min(next,Math.max(50,t.getLong("duration_ms")-LabStore.elapsed(t,now)));}
        for(String key:prefs.getAll().keySet())if(key.startsWith("stage-")&&!stageKeys.contains(key))clean.remove(key);clean.apply();
        delivered.retainAll(valid);c.getSharedPreferences(PREFS,0).edit().putStringSet("delivered",delivered).apply();
        if(next!=Long.MAX_VALUE&&exact(c))manager.setAlarmClock(new AlarmManager.AlarmClockInfo(System.currentTimeMillis()+next,open(c)),pending(c));
    }}catch(Exception ignored){/* UI exposes permission status; stored clocks remain authoritative. */}}
    @android.annotation.SuppressLint("MissingPermission") // notifications() checks runtime permission immediately before posting.
    static JSONArray fireDue(Context c){JSONArray labels=new JSONArray();try{synchronized(LabStore.LOCK){
        JSONObject s=LabStore.load(c);if(s==null||s.optJSONObject("lab")==null)return labels;JSONObject now=LabStore.clock(c);JSONArray timers=s.getJSONObject("lab").getJSONArray("timers");android.content.SharedPreferences prefs=c.getSharedPreferences(PREFS,0);android.content.SharedPreferences.Editor alerts=prefs.edit();Set<String> delivered=new HashSet<>(prefs.getStringSet("delivered",Collections.emptySet()));boolean zh="zh".equals(s.getJSONObject("workspace").getJSONObject("preferences").optString("language"));
        Map<String,Long> stageSent=new HashMap<>();for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);if("staged".equals(t.optString("kind"))){String key="stage-"+t.getString("id")+":"+t.optLong("cycle");long sent=LabStore.alertBaseline(t,prefs.getLong(key,0));stageSent.put(key,sent);alerts.putLong(key,sent);}}
        boolean changed=LabStore.reconcile(s,now);
        for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);String key=t.getString("id")+":"+t.optLong("cycle");if(t.optBoolean("archived"))continue;if("staged".equals(t.optString("kind"))){if("idle".equals(t.optString("status"))||"paused".equals(t.optString("status")))continue;LabStore.Phase p=LabStore.phase(t,now);long sent=stageSent.get("stage-"+key),boundary=LabStore.alertBoundary(t,p);if(boundary>sent){long steps=boundary-(t.optLong("delay_ms")>0?1:0);String label=t.getString("title");if(steps==0)label+=zh?" · 延迟结束，开始第一阶段":" · Delay finished; first stage started";else{JSONArray stages=t.getJSONArray("stages");JSONObject stage=stages.getJSONObject((int)((steps-1)%stages.length()));label+=" · "+stage.getString("title")+" · "+(zh?"第 ":"Cycle ")+((steps-1)/stages.length()+1)+(zh?" 轮":"");label+="waiting".equals(p.kind)?(zh?" · 等待确认":" · Confirm to continue"):(zh?" · 阶段完成":" · Stage finished");if(boundary-sent>1)label+=zh?"（跨越 "+(boundary-sent)+" 个节点）":" ("+(boundary-sent)+" boundaries crossed)";}labels.put(label);alerts.putLong("stage-"+key,boundary);}if(t.optLong("pending_boundary")>0){t.put("pending_boundary",0);changed=true;}continue;}if(!"running".equals(t.optString("status"))||!"countdown".equals(t.optString("kind"))||delivered.contains(key))continue;if(LabStore.elapsed(t,now)>=t.getLong("duration_ms")){labels.put(t.getString("title"));delivered.add(key);}}
        if(changed)LabStore.save(c,s);alerts.putStringSet("delivered",delivered).commit();
        if(labels.length()>0&&notifications(c)){channel(c);StringBuilder body=new StringBuilder();for(int i=0;i<Math.min(labels.length(),4);i++){if(i>0)body.append(" · ");body.append(labels.getString(i));}
            Notification n=new Notification.Builder(c,CHANNEL).setSmallIcon(R.drawable.ic_leaf).setContentTitle(zh?"实验计时已到点":"Experiment timer finished").setContentText(body).setStyle(new Notification.BigTextStyle().bigText(body)).setCategory(Notification.CATEGORY_ALARM).setContentIntent(open(c)).setAutoCancel(true).setNumber(labels.length()).build();c.getSystemService(NotificationManager.class).notify(400,n);
        }
    }}catch(Exception ignored){/* Never corrupt experiment data when alerts are unavailable. */}sync(c);return labels;}
    @Override public void onReceive(Context context,Intent intent){PendingResult pending=goAsync();new Thread(()->{try{fireDue(context);}finally{pending.finish();}},"lab-alarm").start();}
}

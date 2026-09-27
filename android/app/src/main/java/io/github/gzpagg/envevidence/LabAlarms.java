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
    static boolean notifications(Context c){return c.getSystemService(NotificationManager.class).areNotificationsEnabled()&&(Build.VERSION.SDK_INT<33||c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED);}
    static void channel(Context c){NotificationChannel n=new NotificationChannel(CHANNEL,"Experiment timers / 实验计时",NotificationManager.IMPORTANCE_HIGH);n.setDescription("Countdown and sampling reminders / 倒计时与取样提醒");n.enableVibration(true);n.setSound(android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI,new android.media.AudioAttributes.Builder().setUsage(android.media.AudioAttributes.USAGE_ALARM).build());c.getSystemService(NotificationManager.class).createNotificationChannel(n);}
    static PendingIntent pending(Context c){return PendingIntent.getBroadcast(c,0,new Intent(c,LabAlarms.class).setAction("io.github.gzpagg.envevidence.TIMER"),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    static PendingIntent open(Context c){return PendingIntent.getActivity(c,1,new Intent(c,MainActivity.class).putExtra("openTimers",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    @android.annotation.SuppressLint("MissingPermission") // exact() checks the revocable special permission; races are caught.
    static void sync(Context c){try{synchronized(LabStore.LOCK){
        AlarmManager manager=c.getSystemService(AlarmManager.class);manager.cancel(pending(c));JSONObject s=LabStore.load(c);if(s==null||s.optJSONObject("lab")==null)return;
        JSONObject now=LabStore.clock(c);JSONArray timers=s.getJSONObject("lab").getJSONArray("timers");
        Set<String> delivered=new HashSet<>(c.getSharedPreferences(PREFS,0).getStringSet("delivered",Collections.emptySet())),valid=new HashSet<>();long next=Long.MAX_VALUE;
        for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);String key=t.getString("id")+":"+t.optInt("cycle");valid.add(key);if(t.optBoolean("archived")||!"running".equals(t.optString("status"))||!"countdown".equals(t.optString("kind"))||delivered.contains(key))continue;next=Math.min(next,Math.max(50,t.getLong("duration_ms")-LabStore.elapsed(t,now)));}
        delivered.retainAll(valid);c.getSharedPreferences(PREFS,0).edit().putStringSet("delivered",delivered).apply();
        if(next!=Long.MAX_VALUE&&exact(c))manager.setAlarmClock(new AlarmManager.AlarmClockInfo(System.currentTimeMillis()+next,open(c)),pending(c));
    }}catch(Exception ignored){/* UI exposes permission status; stored clocks remain authoritative. */}}
    @android.annotation.SuppressLint("MissingPermission") // notifications() checks runtime permission immediately before posting.
    static JSONArray fireDue(Context c){JSONArray labels=new JSONArray();try{synchronized(LabStore.LOCK){
        JSONObject s=LabStore.load(c);if(s==null||s.optJSONObject("lab")==null)return labels;JSONObject now=LabStore.clock(c);JSONArray timers=s.getJSONObject("lab").getJSONArray("timers");Set<String> delivered=new HashSet<>(c.getSharedPreferences(PREFS,0).getStringSet("delivered",Collections.emptySet()));
        for(int i=0;i<timers.length();i++){JSONObject t=timers.getJSONObject(i);String key=t.getString("id")+":"+t.optInt("cycle");if(t.optBoolean("archived")||!"running".equals(t.optString("status"))||!"countdown".equals(t.optString("kind"))||delivered.contains(key))continue;if(LabStore.elapsed(t,now)>=t.getLong("duration_ms")){labels.put(t.getString("title"));delivered.add(key);}}
        c.getSharedPreferences(PREFS,0).edit().putStringSet("delivered",delivered).commit();
        if(labels.length()>0&&notifications(c)){channel(c);boolean zh="zh".equals(s.getJSONObject("workspace").getJSONObject("preferences").optString("language"));StringBuilder body=new StringBuilder();for(int i=0;i<Math.min(labels.length(),4);i++){if(i>0)body.append(" · ");body.append(labels.getString(i));}
            Notification n=new Notification.Builder(c,CHANNEL).setSmallIcon(R.drawable.ic_leaf).setContentTitle(zh?"实验计时已到点":"Experiment timer finished").setContentText(body).setStyle(new Notification.BigTextStyle().bigText(body)).setCategory(Notification.CATEGORY_ALARM).setContentIntent(open(c)).setAutoCancel(true).setNumber(labels.length()).build();c.getSystemService(NotificationManager.class).notify(400,n);
        }
    }}catch(Exception ignored){/* Never corrupt experiment data when alerts are unavailable. */}sync(c);return labels;}
    @Override public void onReceive(Context context,Intent intent){PendingResult pending=goAsync();new Thread(()->{try{fireDue(context);}finally{pending.finish();}},"lab-alarm").start();}
}

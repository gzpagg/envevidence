package io.github.gzpagg.envevidence;

import android.content.Context;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.AtomicFile;
import org.json.JSONObject;
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
        long value=timer.optLong("elapsed_ms");
        JSONObject anchor=timer.optJSONObject("anchor");
        if("running".equals(timer.optString("status"))&&anchor!=null)
            value+=Math.max(0,anchor.optString("boot").equals(now.optString("boot"))?now.optLong("mono")-anchor.optLong("mono"):now.optLong("wall")-anchor.optLong("wall"));
        return value;
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
        byte[] data=state.toString().getBytes(StandardCharsets.UTF_8);if(data.length>LIMIT)throw new IOException("tooLarge");
        AtomicFile f=file(c);FileOutputStream out=null;try{out=f.startWrite();out.write(data);f.finishWrite(out);}catch(Exception e){if(out!=null)f.failWrite(out);throw new IOException("saveFailed",e);}
    }}
}

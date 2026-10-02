package io.github.gzpagg.envevidence;

import android.content.Context;
import android.graphics.*;
import android.media.ExifInterface;
import android.net.Uri;
import android.util.AtomicFile;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

final class LabPhotos {
    static File dir(Context c){File d=new File(c.getFilesDir(),"photos");if(!d.exists()&&!d.mkdirs())throw new IllegalStateException("file");return d;}
    static File file(Context c,String name) throws Exception {if(!name.matches("[a-f0-9]{32}(\\.thumb)?\\.(jpg|png|webp)"))throw new IOException("invalid");return new File(dir(c),name);}
    static void write(File f,byte[] data) throws Exception {AtomicFile atomic=new AtomicFile(f);FileOutputStream out=null;try{out=atomic.startWrite();out.write(data);atomic.finishWrite(out);}catch(Exception e){if(out!=null)atomic.failWrite(out);throw e;}}
    static JSONObject ingest(Context c,byte[] data,String name,String photoId) throws Exception {
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(data,0,data.length,bounds);
        if(bounds.outWidth<=0||bounds.outHeight<=0||bounds.outMimeType==null)throw new IOException("file");
        String mime=bounds.outMimeType,ext=mime.equals("image/jpeg")?"jpg":mime.equals("image/png")?"png":mime.equals("image/webp")?"webp":null;
        if(ext==null)throw new IOException("imageFormat");
        String id=photoId==null?UUID.randomUUID().toString().replace("-",""):photoId;
        write(file(c,id+"."+ext),data);BitmapFactory.Options opts=new BitmapFactory.Options();opts.inSampleSize=1;while(Math.max(bounds.outWidth,bounds.outHeight)/opts.inSampleSize>1600)opts.inSampleSize*=2;
        Bitmap bitmap=BitmapFactory.decodeByteArray(data,0,data.length,opts);if(bitmap==null)throw new IOException("file");
        Matrix matrix=new Matrix();try{ExifInterface exif=new ExifInterface(new ByteArrayInputStream(data));int o=exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,1);if(o==2)matrix.setScale(-1,1);if(o==3)matrix.setRotate(180);if(o==4){matrix.setRotate(180);matrix.postScale(-1,1);}if(o==5){matrix.setRotate(90);matrix.postScale(-1,1);}if(o==6)matrix.setRotate(90);if(o==7){matrix.setRotate(270);matrix.postScale(-1,1);}if(o==8)matrix.setRotate(270);}catch(IOException ignored){/* Formats without EXIF use their decoded orientation. */}
        Bitmap upright=Bitmap.createBitmap(bitmap,0,0,bitmap.getWidth(),bitmap.getHeight(),matrix,true);ByteArrayOutputStream preview=new ByteArrayOutputStream();upright.compress(Bitmap.CompressFormat.JPEG,88,preview);write(file(c,id+".thumb.jpg"),preview.toByteArray());if(upright!=bitmap)upright.recycle();bitmap.recycle();
        return new JSONObject().put("id",id).put("name",name==null?"photo."+ext:name.substring(0,Math.min(name.length(),300))).put("ext",ext).put("mime",mime).put("bytes",data.length);
    }
    static JSONObject attach(Context c,String recordId,JSONObject photo) throws Exception {synchronized(LabStore.LOCK){JSONObject state=LabStore.load(c);JSONArray rows=state.getJSONObject("lab").getJSONArray("records");for(int i=0;i<rows.length();i++){JSONObject r=rows.getJSONObject(i);if(r.getString("id").equals(recordId)){JSONArray photos=r.getJSONArray("photos");for(int j=0;j<photos.length();j++)if(photos.getJSONObject(j).getString("id").equals(photo.getString("id")))return state;JSONObject recorded=LabStore.clock(c);photo.put("recorded_at",recorded);JSONArray experiments=state.getJSONObject("lab").getJSONArray("experiments");for(int k=0;k<experiments.length();k++){JSONObject e=experiments.getJSONObject(k);if(e.getString("id").equals(r.optString("experiment_id"))){JSONObject until=e.optJSONObject("ended");photo.put("elapsed_ms",LabStore.elapsed(new JSONObject().put("status","running").put("anchor",e.getJSONObject("started")),until==null?recorded:until));break;}}photos.put(photo);state.getJSONObject("lab").getJSONArray("events").put(new JSONObject().put("id",UUID.randomUUID().toString().replace("-","")).put("experiment_id",r.opt("experiment_id")).put("kind","photo_added").put("label",photo.getString("name")).put("at",recorded).put("elapsed_ms",photo.optLong("elapsed_ms",0)));LabStore.save(c,state);return state;}}throw new IOException("invalid");}}
    static Set<String> names(JSONObject state) throws Exception {Set<String> names=new LinkedHashSet<>();JSONObject lab=state.optJSONObject("lab");if(lab!=null){JSONArray rows=lab.getJSONArray("records");for(int i=0;i<rows.length();i++){JSONArray photos=rows.getJSONObject(i).getJSONArray("photos");for(int j=0;j<photos.length();j++){JSONObject p=photos.getJSONObject(j);names.add(p.getString("id")+"."+p.getString("ext"));names.add(p.getString("id")+".thumb.jpg");}}}return names;}
    static void backup(Context c,Uri uri) throws Exception {backup(c,uri,null);}
    static void backup(Context c,Uri uri,String experimentId) throws Exception {
        JSONObject state=LabStore.load(c);if(state==null)throw new IOException("file");
        if(experimentId!=null&&!experimentId.isEmpty()){
            JSONObject lab=state.getJSONObject("lab");boolean found=false;for(String key:new String[]{"experiments","timers","counters","records","events","samples"}){JSONArray source=lab.optJSONArray(key),chosen=new JSONArray();if(source==null)source=new JSONArray();for(int i=0;i<source.length();i++){JSONObject item=source.getJSONObject(i);if(experimentId.equals(item.optString(key.equals("experiments")?"id":"experiment_id"))){chosen.put(item);if(key.equals("experiments"))found=true;}}lab.put(key,chosen);}if(!found)throw new IOException("invalid");
            state.put("projects",new JSONArray());JSONObject workspace=state.getJSONObject("workspace");for(String key:new String[]{"goals","tasks","notes"})workspace.put(key,new JSONArray());lab.put("demo_loaded",false);
        }
        byte[] json=state.toString(2).getBytes(StandardCharsets.UTF_8);long total=json.length;for(String name:names(state)){File f=file(c,name);if(!f.isFile())throw new IOException("missingPhoto");total+=f.length();}if(total>512L*1024*1024)throw new IOException("backupLimit");
        try(OutputStream raw=c.getContentResolver().openOutputStream(uri,"wt");ZipOutputStream out=new ZipOutputStream(raw)){
            out.putNextEntry(new ZipEntry("workspace.json"));out.write(json);out.closeEntry();
            for(String name:names(state)){out.putNextEntry(new ZipEntry("photos/"+name));try(InputStream in=new FileInputStream(file(c,name))){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}out.closeEntry();}
        }
    }
    static JSONObject restore(Context c,Uri uri) throws Exception {
        try(BufferedInputStream input=new BufferedInputStream(c.getContentResolver().openInputStream(uri))){
            input.mark(4);int first=input.read();input.reset();if(first!='P')return new JSONObject(new String(LabStore.read(input,LabStore.LIMIT),StandardCharsets.UTF_8));
            try(ZipInputStream zip=new ZipInputStream(input)){ZipEntry entry;JSONObject state=null;long total=0;Set<String> seen=new HashSet<>();
                while((entry=zip.getNextEntry())!=null){String path=entry.getName();if(!seen.add(path)||entry.isDirectory()||(!path.equals("workspace.json")&&!path.matches("photos/[a-f0-9]{32}(\\.thumb)?\\.(jpg|png|webp)")))throw new IOException("invalid");
                    ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=zip.read(b))!=-1){total+=n;if(total>512L*1024*1024||data.size()+n>LabStore.LIMIT)throw new IOException("tooLarge");data.write(b,0,n);}byte[] bytes=data.toByteArray();
                    if(path.equals("workspace.json"))state=new JSONObject(new String(bytes,StandardCharsets.UTF_8));else{File f=file(c,path.substring(7));if(f.exists()){if(!Arrays.equals(bytes,LabStore.read(new FileInputStream(f),LabStore.LIMIT)))throw new IOException("photoConflict");}else write(f,bytes);}zip.closeEntry();
                }
                if(state==null)throw new IOException("invalid");for(String name:names(state))if(!file(c,name).isFile())throw new IOException("missingPhoto");return state;
            }
        }
    }
}

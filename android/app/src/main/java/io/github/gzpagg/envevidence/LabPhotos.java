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
        return new JSONObject().put("id",id).put("name",name==null?"photo."+ext:name.substring(0,Math.min(name.length(),300))).put("ext",ext).put("mime",mime).put("bytes",data.length).put("sha256",LabAudio.sha256(file(c,id+"."+ext)));
    }
    static JSONObject attach(Context c,String recordId,JSONObject photo) throws Exception {synchronized(LabStore.LOCK){JSONObject state=LabStore.load(c);JSONArray rows=state.getJSONObject("lab").getJSONArray("records");for(int i=0;i<rows.length();i++){JSONObject r=rows.getJSONObject(i);if(r.getString("id").equals(recordId)){JSONArray photos=r.getJSONArray("photos");for(int j=0;j<photos.length();j++)if(photos.getJSONObject(j).getString("id").equals(photo.getString("id")))return state;JSONObject recorded=LabStore.clock(c);photo.put("recorded_at",recorded);JSONArray experiments=state.getJSONObject("lab").getJSONArray("experiments");for(int k=0;k<experiments.length();k++){JSONObject e=experiments.getJSONObject(k);if(e.getString("id").equals(r.optString("experiment_id"))){JSONObject until=e.optJSONObject("ended");photo.put("elapsed_ms",LabStore.elapsed(new JSONObject().put("status","running").put("anchor",e.getJSONObject("started")),until==null?recorded:until));break;}}photos.put(photo);state.getJSONObject("lab").getJSONArray("events").put(new JSONObject().put("id",UUID.randomUUID().toString().replace("-","")).put("experiment_id",r.opt("experiment_id")).put("kind","photo_added").put("record_id",recordId).put("photo_id",photo.getString("id")).put("label",photo.getString("name")).put("at",recorded).put("elapsed_ms",photo.optLong("elapsed_ms",0)));LabStore.save(c,state);return state;}}throw new IOException("invalid");}}
    static Set<String> names(JSONObject state) throws Exception {Set<String> names=new LinkedHashSet<>();JSONObject lab=state.optJSONObject("lab");if(lab!=null){JSONArray rows=lab.getJSONArray("records");for(int i=0;i<rows.length();i++){JSONArray photos=rows.getJSONObject(i).getJSONArray("photos");for(int j=0;j<photos.length();j++){JSONObject p=photos.getJSONObject(j);names.add(p.getString("id")+"."+p.getString("ext"));names.add(p.getString("id")+".thumb.jpg");}}}return names;}
    static final long BACKUP_LIMIT=512L*1024*1024;
    static Map<String,JSONObject> media(JSONObject state) throws Exception {
        Map<String,JSONObject> refs=new LinkedHashMap<>();JSONObject lab=state.optJSONObject("lab");if(lab==null)return refs;JSONArray records=lab.getJSONArray("records");
        for(int i=0;i<records.length();i++){JSONObject r=records.getJSONObject(i);JSONArray photos=r.optJSONArray("photos");if(photos==null)throw new IOException("invalid");Set<String> ids=new HashSet<>();
            for(int j=0;j<photos.length();j++){JSONObject p=photos.getJSONObject(j);String id=p.getString("id"),ext=p.getString("ext");if(!id.matches("[a-f0-9]{32}")||!ext.matches("jpg|png|webp")||!ids.add(id))throw new IOException("invalid");String path="photos/"+id+"."+ext;putRef(refs,path,p);refs.put("photos/"+id+".thumb.jpg",null);}
            JSONArray audios=r.optJSONArray("audios");ids.clear();if(audios!=null)for(int j=0;j<audios.length();j++){JSONObject v=audios.getJSONObject(j);String id=v.getString("id");if(!id.matches("[a-f0-9]{32}")||!"m4a".equals(v.getString("ext"))||!"audio/mp4".equals(v.getString("mime"))||!ids.add(id)||!v.optString("sha256").matches("[a-f0-9]{64}")||v.optLong("duration_ms")<=0||v.optLong("duration_ms")>LabAudio.MAX_DURATION_MS+2000)throw new IOException("invalid");putRef(refs,"audio/"+id+".m4a",v);}
        }return refs;
    }
    private static void putRef(Map<String,JSONObject> refs,String path,JSONObject item) throws Exception {if(item.optLong("bytes")<=0||item.optLong("bytes")>LabStore.LIMIT)throw new IOException("invalid");if(item.has("sha256")&&!item.optString("sha256").matches("[a-f0-9]{64}"))throw new IOException("invalid");JSONObject before=refs.get(path);if(before!=null&&(before.getLong("bytes")!=item.getLong("bytes")||!before.optString("sha256").equals(item.optString("sha256"))))throw new IOException(path.startsWith("audio/")?"audioConflict":"photoConflict");refs.put(path,item);}
    private static File mediaFile(Context c,String path) throws Exception {if(path.startsWith("photos/"))return file(c,path.substring(7));if(path.startsWith("audio/"))return LabAudio.file(c,path.substring(6));throw new IOException("invalid");}
    private static String missing(String path){return path.startsWith("audio/")?"missingAudio":"missingPhoto";}
    private static String conflict(String path){return path.startsWith("audio/")?"audioConflict":"photoConflict";}
    static void backup(Context c,Uri uri) throws Exception {backup(c,uri,null);}
    static void backup(Context c,Uri uri,String experimentId) throws Exception {
        JSONObject state=LabStore.load(c);if(state==null)throw new IOException("file");
        if(experimentId!=null&&!experimentId.isEmpty()){
            JSONObject lab=state.getJSONObject("lab");boolean found=false;
            for(String key:new String[]{"experiments","timers","counters","records","events","samples","workflows"}){JSONArray source=lab.optJSONArray(key),chosen=new JSONArray();if(source==null)continue;for(int i=0;i<source.length();i++){JSONObject item=source.getJSONObject(i);if(experimentId.equals(item.optString(key.equals("experiments")?"id":"experiment_id"))){chosen.put(item);if(key.equals("experiments"))found=true;}}lab.put(key,chosen);}if(!found)throw new IOException("invalid");
            // A single experiment carries its own snapshots and only their referenced templates.
            Set<String> templateIds=new HashSet<>();JSONArray flows=lab.optJSONArray("workflows");
            if(flows!=null)for(int i=0;i<flows.length();i++){String template=flows.getJSONObject(i).optString("template_id",null);if(template!=null&&!template.isEmpty())templateIds.add(template);}
            JSONArray library=lab.optJSONArray("experiment_templates"),linked=new JSONArray();
            if(library!=null)for(int i=0;i<library.length();i++){JSONObject template=library.getJSONObject(i);if(templateIds.contains(template.optString("id")))linked.put(template);}
            lab.put("experiment_templates",linked).put("observation_phrases",new JSONArray());
            state.put("projects",new JSONArray());JSONObject workspace=state.getJSONObject("workspace");for(String key:new String[]{"goals","tasks","notes"})workspace.put(key,new JSONArray());lab.put("demo_loaded",false);
        }
        Map<String,JSONObject> refs=media(state);JSONObject files=new JSONObject();long total=0;
        for(Map.Entry<String,JSONObject> e:refs.entrySet()){String path=e.getKey();File f=mediaFile(c,path);if(!f.isFile())throw new IOException(missing(path));if(f.length()>LabStore.LIMIT||f.length()==0)throw new IOException("tooLarge");String sha=LabAudio.sha256(f);JSONObject meta=e.getValue();if(meta!=null){if(meta.has("sha256")&&!sha.equals(meta.getString("sha256")))throw new IOException("mediaChecksum");if(meta.getLong("bytes")!=f.length())throw new IOException("mediaChecksum");meta.put("sha256",sha);}files.put(path,new JSONObject().put("bytes",f.length()).put("sha256",sha));total+=f.length();}
        byte[] json=state.toString(2).getBytes(StandardCharsets.UTF_8);JSONObject manifest=new JSONObject().put("format","envevidence-media").put("version",1).put("workspace_sha256",LabAudio.sha256(new ByteArrayInputStream(json))).put("files",files);byte[] manifestBytes=manifest.toString(2).getBytes(StandardCharsets.UTF_8);total+=json.length+manifestBytes.length;if(json.length>LabStore.LIMIT||manifestBytes.length>LabStore.LIMIT||refs.size()>9998)throw new IOException("backupLimit");if(total>BACKUP_LIMIT)throw new IOException("backupLimit");
        try(OutputStream raw=c.getContentResolver().openOutputStream(uri,"wt")){if(raw==null)throw new IOException("file");try(ZipOutputStream out=new ZipOutputStream(raw)){out.putNextEntry(new ZipEntry("workspace.json"));out.write(json);out.closeEntry();out.putNextEntry(new ZipEntry("media-manifest.json"));out.write(manifestBytes);out.closeEntry();for(String path:refs.keySet()){out.putNextEntry(new ZipEntry(path));try(InputStream in=new FileInputStream(mediaFile(c,path))){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}out.closeEntry();}}}
    }
    private static void validateBackup(JSONObject state) throws Exception {
        if(!"envevidence-android".equals(state.optString("format"))||state.optInt("schema_version")!=1||state.optJSONObject("workspace")==null||state.optJSONArray("projects")==null)throw new IOException("invalid");
        JSONObject lab=state.optJSONObject("lab");if(lab==null)return;if(lab.optInt("version")!=1&&lab.optInt("version")!=2)throw new IOException("invalid");Set<String> experiments=new HashSet<>();JSONArray es=lab.getJSONArray("experiments");for(int i=0;i<es.length();i++)experiments.add(es.getJSONObject(i).getString("id"));
        for(String key:new String[]{"experiments","timers","counters","records","events","samples","workflows","experiment_templates","observation_phrases"}){JSONArray items=lab.optJSONArray(key);if(items==null){if(Arrays.asList("experiments","timers","counters","records","events").contains(key))throw new IOException("invalid");continue;}Set<String> ids=new HashSet<>();for(int i=0;i<items.length();i++){JSONObject item=items.getJSONObject(i);String id=item.getString("id");if(!id.matches("[a-f0-9]{32}")||!ids.add(id))throw new IOException("invalid");if(!key.equals("experiments")&&!key.equals("experiment_templates")&&!key.equals("observation_phrases")&&!item.isNull("experiment_id")&&!experiments.contains(item.optString("experiment_id")))throw new IOException("invalid");}}
        media(state); // Validate original filenames and attachment metadata, including legacy photos.
    }
    static JSONObject restore(Context c,Uri uri) throws Exception {
        InputStream source=c.getContentResolver().openInputStream(uri);if(source==null)throw new IOException("file");
        try(BufferedInputStream input=new BufferedInputStream(source)){
            input.mark(4);int first=input.read();input.reset();if(first!='P')return new JSONObject(new String(LabStore.read(input,LabStore.LIMIT),StandardCharsets.UTF_8));
            File staging=new File(c.getCacheDir(),"media-import-"+UUID.randomUUID());if(!staging.mkdirs())throw new IOException("file");List<File> added=new ArrayList<>();boolean committed=false;
            try {
                Map<String,File> staged=new LinkedHashMap<>();Map<String,String> hashes=new HashMap<>();Map<String,Long> lengths=new HashMap<>();JSONObject state=null,manifest=null;String workspaceSha=null;long total=0;
                try(ZipInputStream zip=new ZipInputStream(input)){ZipEntry entry;int count=0;
                    while((entry=zip.getNextEntry())!=null){String path=entry.getName();if(++count>10000||staged.containsKey(path)||entry.isDirectory()||!(path.equals("workspace.json")||path.equals("media-manifest.json")||path.matches("photos/[a-f0-9]{32}(\\.thumb)?\\.(jpg|png|webp)")||path.matches("audio/[a-f0-9]{32}\\.m4a")))throw new IOException("invalid");
                        File target=new File(staging,Integer.toString(count));long size=0;try(OutputStream out=new FileOutputStream(target)){byte[] b=new byte[8192];int n;while((n=zip.read(b))!=-1){size+=n;total+=n;if(total>BACKUP_LIMIT||size>LabStore.LIMIT)throw new IOException("tooLarge");out.write(b,0,n);}}
                        staged.put(path,target);String hash=LabAudio.sha256(target);hashes.put(path,hash);lengths.put(path,size);
                        if(path.equals("workspace.json")){state=new JSONObject(new String(LabStore.read(new FileInputStream(target),LabStore.LIMIT),StandardCharsets.UTF_8));workspaceSha=hash;}else if(path.equals("media-manifest.json"))manifest=new JSONObject(new String(LabStore.read(new FileInputStream(target),LabStore.LIMIT),StandardCharsets.UTF_8));zip.closeEntry();
                    }
                } catch(ZipException e) { // Android's path validator may reject traversal before our entry check.
                    throw new IOException("invalid",e);
                }
                if(state==null)throw new IOException("invalid");validateBackup(state);Map<String,JSONObject> refs=media(state);
                for(String path:staged.keySet())if(!path.equals("workspace.json")&&!path.equals("media-manifest.json")&&!refs.containsKey(path))throw new IOException("invalid");
                if(manifest!=null){if(!"envevidence-media".equals(manifest.optString("format"))||manifest.optInt("version")!=1||!Objects.equals(workspaceSha,manifest.optString("workspace_sha256")))throw new IOException("mediaChecksum");JSONObject list=manifest.getJSONObject("files");if(list.length()!=refs.size())throw new IOException("mediaChecksum");for(String path:refs.keySet()){JSONObject check=list.optJSONObject(path);if(check==null||!Objects.equals(hashes.get(path),check.optString("sha256"))||!Objects.equals(lengths.get(path),check.optLong("bytes")))throw new IOException("mediaChecksum");}}
                for(Map.Entry<String,JSONObject> e:refs.entrySet()){String path=e.getKey();if(!staged.containsKey(path))throw new IOException(missing(path));JSONObject metadata=e.getValue();if(metadata!=null){if(metadata.getLong("bytes")!=lengths.get(path)||(metadata.has("sha256")&&!metadata.getString("sha256").equals(hashes.get(path))))throw new IOException("mediaChecksum");}
                    File f=mediaFile(c,path);if(f.exists()&&(f.length()!=lengths.get(path)||!LabAudio.sha256(f).equals(hashes.get(path))))throw new IOException(conflict(path));
                }
                synchronized(LabStore.LOCK){ // Check again under the same lock before committing new originals.
                    for(String path:refs.keySet()){File f=mediaFile(c,path);if(f.exists()&&(f.length()!=lengths.get(path)||!LabAudio.sha256(f).equals(hashes.get(path))))throw new IOException(conflict(path));}
                    for(String path:refs.keySet()){File f=mediaFile(c,path);if(f.exists())continue;File from=staged.get(path);if(!from.renameTo(f)){try(InputStream in=new FileInputStream(from)){write(f,LabStore.read(in,LabStore.LIMIT));}}added.add(f);}
                    committed=true;
                }return state;
            } finally { if(!committed)for(File f:added)f.delete();File[] temp=staging.listFiles();if(temp!=null)for(File f:temp)f.delete();staging.delete(); }
        }
    }
}

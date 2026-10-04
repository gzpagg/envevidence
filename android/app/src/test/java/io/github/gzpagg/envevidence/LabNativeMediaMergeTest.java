package io.github.gzpagg.envevidence;

import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;

/** A stale WebView save must not erase native media files' observation audit. */
public class LabNativeMediaMergeTest {
    private JSONObject state(boolean includeRecord) throws Exception {
        JSONObject lab=new JSONObject().put("timers",new JSONArray()).put("records",new JSONArray()).put("events",new JSONArray());
        if(includeRecord)lab.getJSONArray("records").put(new JSONObject().put("id","a".repeat(32)).put("experiment_id","b".repeat(32)).put("photos",new JSONArray()).put("audios",new JSONArray()));
        return new JSONObject().put("lab",lab);
    }
    private JSONObject event(String kind,String id,String attachment) throws Exception {
        return new JSONObject().put("id",id.repeat(32)).put("experiment_id","b".repeat(32)).put("kind",kind).put("record_id","a".repeat(32)).put(kind.equals("audio_added")?"audio_id":"photo_id",attachment.repeat(32));
    }
    @Test public void staleSnapshotRetainsAudioMetadataAndItsNativeEventExactlyOnce() throws Exception {
        JSONObject old=state(true),current=state(true);old.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").put(new JSONObject().put("id","c".repeat(32)).put("sha256","d".repeat(64)));
        old.getJSONObject("lab").getJSONArray("events").put(event("audio_added","e","c"));
        LabStore.preserveNative(current,old);assertEquals(1,current.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").length());assertEquals(1,current.getJSONObject("lab").getJSONArray("events").length());
        LabStore.preserveNative(current,old);assertEquals(1,current.getJSONObject("lab").getJSONArray("events").length());
    }
    @Test public void photoAuditRequiresItsAttachmentAndDeletedRecordsAreNotRevived() throws Exception {
        JSONObject old=state(true);old.getJSONObject("lab").getJSONArray("events").put(event("photo_added","e","c"));
        JSONObject current=state(true);LabStore.preserveNative(current,old);assertEquals(0,current.getJSONObject("lab").getJSONArray("events").length());
        current.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("photos").put(new JSONObject().put("id","c".repeat(32)));LabStore.preserveNative(current,old);assertEquals(1,current.getJSONObject("lab").getJSONArray("events").length());
        JSONObject removed=state(false);LabStore.preserveNative(removed,old);assertEquals(0,removed.getJSONObject("lab").getJSONArray("records").length());assertEquals(0,removed.getJSONObject("lab").getJSONArray("events").length());
    }
    @Test public void sameAudioIdWithDifferentHashRejectsStaleOverwrite() throws Exception {
        JSONObject old=state(true),current=state(true);old.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").put(new JSONObject().put("id","c".repeat(32)).put("sha256","d".repeat(64)));current.getJSONObject("lab").getJSONArray("records").getJSONObject(0).getJSONArray("audios").put(new JSONObject().put("id","c".repeat(32)).put("sha256","f".repeat(64)));
        try{LabStore.preserveNative(current,old);fail("Conflicting audio must reject save");}catch(java.io.IOException e){assertEquals("audioConflict",e.getMessage());}
    }
}

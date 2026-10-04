package io.github.gzpagg.envevidence;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

/** Same fixtures and active-time units as android/tests/staged-timers.test.cjs. */
public class LabTimerSemanticsTest {
    private JSONObject clock(long elapsed) throws Exception {
        return new JSONObject().put("wall",1700000000000L+elapsed).put("mono",10000L+elapsed).put("boot","boot1");
    }
    private JSONObject state(String mode) throws Exception {
        JSONObject timer=new JSONObject().put("id","a".repeat(32)).put("experiment_id","b".repeat(32)).put("title","Oxidation").put("kind","staged").put("status","running").put("elapsed_ms",0).put("anchor",clock(0)).put("cycle",0).put("archived",false).put("duration_ms",6500).put("delay_ms",500).put("repeat_count",2).put("transition_mode",mode).put("completed_steps",0).put("audit_cursor",0).put("stages",new JSONArray().put(new JSONObject().put("title","Mix").put("duration_ms",1000)).put(new JSONObject().put("title","React").put("duration_ms",2000)));
        JSONObject experiment=new JSONObject().put("id","b".repeat(32)).put("started",clock(0)).put("ended",JSONObject.NULL);
        return new JSONObject().put("lab",new JSONObject().put("timers",new JSONArray().put(timer)).put("experiments",new JSONArray().put(experiment)).put("events",new JSONArray()).put("records",new JSONArray()));
    }
    private JSONObject timer(JSONObject state) throws Exception {return state.getJSONObject("lab").getJSONArray("timers").getJSONObject(0);}
    private JSONObject lastEvent(JSONObject state) throws Exception {JSONArray events=state.getJSONObject("lab").getJSONArray("events");return events.getJSONObject(events.length()-1);}

    @Test public void delayedAutoRecoverySeparatesBoundaryFromObservation() throws Exception {
        JSONObject state=state("auto");assertTrue(LabStore.reconcile(state,clock(1600)));JSONObject event=lastEvent(state);
        assertEquals("timer_progress",event.getString("kind"));assertEquals(1700000001500L,event.getJSONObject("at").getLong("wall"));assertEquals(11500L,event.getJSONObject("at").getLong("mono"));assertEquals(1500L,event.getLong("elapsed_ms"));assertEquals(1500L,event.getLong("timer_elapsed_ms"));assertEquals(1600L,event.getLong("observed_elapsed_ms"));assertEquals(1700000001600L,event.getJSONObject("observed_at").getLong("wall"));assertEquals(2L,event.getLong("boundary_count"));
        assertFalse(LabStore.reconcile(state,clock(1600)));assertEquals(1,state.getJSONObject("lab").getJSONArray("events").length());
    }
    @Test public void exactDelayAndStageBoundariesHaveEqualEventAndObservedValues() throws Exception {
        JSONObject state=state("auto");for(long elapsed:new long[]{500,1500}){assertTrue(LabStore.reconcile(state,clock(elapsed)));JSONObject event=lastEvent(state);assertEquals(elapsed,event.getLong("timer_elapsed_ms"));assertEquals(elapsed,event.getLong("observed_elapsed_ms"));assertEquals(elapsed,event.getLong("elapsed_ms"));assertEquals(clock(elapsed).getLong("wall"),event.getJSONObject("at").getLong("wall"));assertEquals(clock(elapsed).getLong("mono"),event.getJSONObject("observed_at").getLong("mono"));}
    }
    @Test public void manualDeadlineFreezesAcrossRestartsUntilAConfirmedNewAnchor() throws Exception {
        JSONObject state=state("manual");assertTrue(LabStore.reconcile(state,clock(10000)));assertEquals("waiting",timer(state).getString("status"));assertEquals(1500L,timer(state).getLong("elapsed_ms"));assertTrue(timer(state).isNull("anchor"));assertEquals(1500L,lastEvent(state).getLong("timer_elapsed_ms"));assertEquals(10000L,lastEvent(state).getJSONObject("observed_at").getLong("mono")-10000L);
        JSONObject restart=new JSONObject(state.toString());LabStore.Phase waiting=LabStore.phase(timer(restart),clock(100000));assertEquals("waiting",waiting.kind);assertEquals(1500L,waiting.elapsed);assertEquals(-1L,waiting.next);assertFalse(LabStore.reconcile(restart,clock(100000)));assertEquals(0L,timer(restart).getLong("completed_steps"));
        timer(restart).put("completed_steps",1).put("status","running").put("anchor",clock(100000));LabStore.Phase next=LabStore.phase(timer(restart),clock(101000));assertEquals(1000L,next.remaining);assertEquals(1L,next.stage);assertEquals(2500L,next.elapsed);
    }
    @Test public void staleSnapshotPreservesNativeAuditCursorWithoutDuplicatingBoundaries() throws Exception {
        JSONObject stale=state("auto"),stored=new JSONObject(stale.toString());LabStore.reconcile(stored,clock(1600));LabStore.preserveNative(stale,stored);assertEquals(2L,timer(stale).getLong("audit_cursor"));assertEquals(1,stale.getJSONObject("lab").getJSONArray("events").length());assertFalse(LabStore.reconcile(stale,clock(1700)));LabStore.preserveNative(stale,stored);assertEquals(1,stale.getJSONObject("lab").getJSONArray("events").length());
        JSONObject equivalent=state("auto");LabStore.reconcile(equivalent,clock(1600));LabStore.preserveNative(equivalent,stored);assertEquals(1,equivalent.getJSONObject("lab").getJSONArray("events").length());
    }
}

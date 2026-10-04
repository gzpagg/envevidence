package io.github.gzpagg.envevidence;

import org.junit.Test;
import java.io.IOException;
import static org.junit.Assert.*;

public class LabAudioRangeTest {
    @Test public void fullAndOpenRangesRespectOriginalLength() throws Exception {
        LabAudio.ByteRange full=LabAudio.range(null,100);assertEquals(0,full.start);assertEquals(99,full.end);assertEquals(100,full.length());
        LabAudio.ByteRange open=LabAudio.range("bytes=12-",100);assertEquals(12,open.start);assertEquals(99,open.end);assertEquals(88,open.length());
        assertEquals(99,LabAudio.range("bytes=20-200",100).end);
    }
    @Test public void suffixRangesAreClampedToOriginal() throws Exception {
        LabAudio.ByteRange suffix=LabAudio.range("bytes=-7",100);assertEquals(93,suffix.start);assertEquals(99,suffix.end);
        assertEquals(0,LabAudio.range("bytes=-101",100).start);
    }
    @Test public void invalidRangesCannotSelectOutsideFile() throws Exception {
        for(String r:new String[]{"bytes=100-","bytes=20-19","bytes=-0","bytes=0-2,4-8","bytes=+-2","items=0-2","bytes=999999999999999999999999-"}){
            try{LabAudio.range(r,100);fail("Should reject "+r);}catch(IOException expected){assertEquals("range",expected.getMessage());}
        }
        try{LabAudio.range(null,0);fail("Empty file has no valid range");}catch(IOException expected){assertEquals("range",expected.getMessage());}
    }
}

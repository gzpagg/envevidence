import com.android.apksig.ApkSigner;
import com.android.apksig.ApkVerifier;
import java.io.File;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.List;

/** Local release signing. The keystore and password must never be committed. */
public class SignApk {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("unsigned.apk signed.apk keystore.p12");
        String value = System.getenv("ENVEVIDENCE_SIGNING_PASSWORD");
        if (value == null) throw new IllegalArgumentException("Set ENVEVIDENCE_SIGNING_PASSWORD locally");
        char[] password = value.toCharArray();
        KeyStore store = KeyStore.getInstance("PKCS12");
        try (FileInputStream in = new FileInputStream(args[2])) { store.load(in, password); }
        PrivateKey key = (PrivateKey) store.getKey("envevidence", password);
        X509Certificate certificate = (X509Certificate) store.getCertificate("envevidence");
        ApkSigner.SignerConfig signer = new ApkSigner.SignerConfig.Builder("envevidence", key, List.of(certificate)).build();
        new ApkSigner.Builder(List.of(signer)).setInputApk(new File(args[0])).setOutputApk(new File(args[1]))
            .setV1SigningEnabled(true).setV2SigningEnabled(true).setV3SigningEnabled(true).build().sign();
        ApkVerifier.Result result = new ApkVerifier.Builder(new File(args[1])).build().verify();
        if (!result.isVerified()) throw new IllegalStateException("APK signature verification failed: "+result.getErrors());
        System.out.println("APK verified: v1="+result.isVerifiedUsingV1Scheme()+", v2="+result.isVerifiedUsingV2Scheme()+", v3="+result.isVerifiedUsingV3Scheme());
        java.util.Arrays.fill(password, '\0');
    }
}

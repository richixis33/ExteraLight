package com.exteragram.messenger.boost.encryption;

import org.telegram.messenger.MessageObject;

public class EncryptionHelper {

    public static final CharSequence[] names = new CharSequence[]{"AES-256", "ChaCha20", "ExteraSecure"};

    public interface EncryptionCallback {
        void onEncrypted(String message);
    }

    public static boolean isEncrypted(MessageObject messageObject, Object obj) {
        return false;
    }

    public static boolean isEncrypted(MessageObject messageObject) {
        return false;
    }

    public static boolean isEncrypted(String text) {
        return false;
    }

    public static BaseEncryptor getEncryptorBy(long dialogId) {
        return new BaseEncryptor();
    }

    public static int getEncryptorTypeFor(long dialogId) {
        return 0;
    }

    public static void setEncryptorTypeFor(long dialogId, int type) {
    }

    public static void encryptMessage(String text, long dialogId, int type, EncryptionCallback callback) {
        if (callback != null) {
            callback.onEncrypted(text);
        }
    }

    public static String encryptMessage(String text, long dialogId, BaseEncryptor encryptor) {
        return text;
    }

    public static MessageObject decryptMessage(MessageObject messageObject, Object group) {
        return messageObject;
    }

    public static MessageObject decryptMessage(MessageObject messageObject, MessageObject.GroupedMessages group) {
        return messageObject;
    }

    public static MessageObject decryptMessage(MessageObject messageObject) {
        return messageObject;
    }
}

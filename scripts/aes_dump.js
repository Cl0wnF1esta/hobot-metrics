Java.perform(function () {
    var Cipher = Java.use("javax.crypto.Cipher");

    Cipher.doFinal.overload("[B").implementation = function (input) {
        var result = this.doFinal(input);
        try {
            var resultStr = Java.use("java.lang.String").$new(result, "UTF-8");
            console.log("\n===== Cipher.doFinal output =====\n" + resultStr);
        } catch (e) {
            console.log("\n===== Cipher.doFinal output [binary, " + result.length + " bytes] =====");
        }
        return result;
    };

    Cipher.doFinal.overload("[B", "int", "int").implementation = function (input, offset, len) {
        var result = this.doFinal(input, offset, len);
        try {
            var resultStr = Java.use("java.lang.String").$new(result, "UTF-8");
            console.log("\n===== Cipher.doFinal output =====\n" + resultStr);
        } catch (e) {
            console.log("\n===== Cipher.doFinal output [binary, " + result.length + " bytes] =====");
        }
        return result;
    };

    console.log("[+] Cipher.doFinal hooked");
});

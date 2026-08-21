function extractPrintableStrings(buf, len, minLen) {
    minLen = minLen || 6;
    const bytes = new Uint8Array(buf.readByteArray(len));
    let results = [];
    let current = "";
    for (let i = 0; i < bytes.length; i++) {
        const b = bytes[i];
        if (b >= 0x20 && b <= 0x7e) {
            current += String.fromCharCode(b);
        } else {
            if (current.length >= minLen) {
                results.push(current);
            }
            current = "";
        }
    }
    if (current.length >= minLen) {
        results.push(current);
    }
    return results;
}

function hookLib(libname) {
    const mod = Process.findModuleByName(libname);
    if (!mod) {
        console.log("[-] Module not loaded (yet?): " + libname);
        return;
    }

    const writePtr = mod.findExportByName("SSL_write");
    const readPtr = mod.findExportByName("SSL_read");

    if (writePtr) {
        Interceptor.attach(writePtr, {
            onEnter(args) {
                this.buf = args[1];
                this.num = args[2].toInt32();
            },
            onLeave(retval) {
                const n = retval.toInt32();
                if (n > 0) {
                    const strs = extractPrintableStrings(this.buf, n);
                    if (strs.length > 0) {
                        console.log("\n===== SSL_write (" + libname + ", " + n + " bytes) =====");
                        strs.forEach(s => console.log("  " + s));
                    }
                }
            }
        });
        console.log("[+] Hooked SSL_write in " + libname);
    }

    if (readPtr) {
        Interceptor.attach(readPtr, {
            onEnter(args) {
                this.buf = args[1];
            },
            onLeave(retval) {
                const n = retval.toInt32();
                if (n > 0) {
                    const strs = extractPrintableStrings(this.buf, n);
                    if (strs.length > 0) {
                        console.log("\n===== SSL_read (" + libname + ", " + n + " bytes) =====");
                        strs.forEach(s => console.log("  " + s));
                    }
                }
            }
        });
        console.log("[+] Hooked SSL_read in " + libname);
    }
}

setTimeout(function () {
    hookLib("libssl.1.1.so");
    hookLib("libssl.so");
}, 500);

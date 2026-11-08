import os
import re
import sys
import struct
import subprocess

def patch_arsc_strings(arsc_data, replacements):
    try:
        main_type, main_hsize, main_fsize, main_pkg_cnt = struct.unpack_from('<HHII', arsc_data, 0)
        sp_off = 12
        stype, ssize, scsize, scount, style_cnt, flags, sstart, styles_start = struct.unpack_from('<HHIIIIII', arsc_data, sp_off)
        offsets = list(struct.unpack_from(f'<{scount}I', arsc_data, sp_off + ssize))

        strings_bytes_start = sp_off + sstart
        styles_bytes_start = sp_off + styles_start if style_cnt > 0 else sp_off + scsize

        strings = []
        is_utf8 = (flags & (1 << 8)) != 0

        for i in range(scount):
            off = offsets[i]
            sdata = arsc_data[strings_bytes_start + off:]
            idx = 0
            if sdata[idx] & 0x80: idx += 2
            else: idx += 1
            if sdata[idx] & 0x80: idx += 2
            else: idx += 1
            end = sdata.find(b'\x00', idx)
            s_val = sdata[idx:end].decode('utf-8', errors='ignore')
            strings.append(s_val)

        changed = 0
        for i in range(len(strings)):
            for old_txt, new_txt in replacements.items():
                if old_txt in strings[i]:
                    strings[i] = strings[i].replace(old_txt, new_txt)
                    changed += 1

        print(f"Patched {changed} strings in resources.arsc string pool")

        new_strings_data = bytearray()
        new_offsets = []
        for s in strings:
            new_offsets.append(len(new_strings_data))
            encoded = s.encode('utf-8')
            char_len = len(s)
            byte_len = len(encoded)
            buf = bytearray()
            if char_len > 127:
                buf.append(((char_len >> 8) & 0x7f) | 0x80)
                buf.append(char_len & 0xff)
            else:
                buf.append(char_len)
            if byte_len > 127:
                buf.append(((byte_len >> 8) & 0x7f) | 0x80)
                buf.append(byte_len & 0xff)
            else:
                buf.append(byte_len)
            buf.extend(encoded)
            buf.append(0)
            new_strings_data.extend(buf)

        pad = (4 - (len(new_strings_data) % 4)) % 4
        new_strings_data.extend(b'\x00' * pad)

        styles_data = arsc_data[styles_bytes_start:sp_off + scsize]

        new_sstart = ssize + (scount * 4) + (style_cnt * 4)
        new_sstart_pad = (4 - (new_sstart % 4)) % 4
        new_sstart += new_sstart_pad

        new_styles_start = new_sstart + len(new_strings_data) if style_cnt > 0 else 0
        new_scsize = new_sstart + len(new_strings_data) + len(styles_data)

        new_sp_header = struct.pack('<HHIIIIII', stype, ssize, new_scsize, scount, style_cnt, flags, new_sstart, new_styles_start)
        new_offsets_bytes = struct.pack(f'<{scount}I', *new_offsets)
        styles_offsets_bytes = arsc_data[sp_off + ssize + scount * 4 : sp_off + ssize + scount * 4 + style_cnt * 4]

        new_sp = new_sp_header + new_offsets_bytes + styles_offsets_bytes + (b'\x00' * new_sstart_pad) + new_strings_data + styles_data
        remainder = arsc_data[sp_off + scsize:]

        new_arsc = arsc_data[:sp_off] + new_sp + remainder
        new_fsize = len(new_arsc)
        new_arsc = struct.pack('<HHII', main_type, main_hsize, new_fsize, main_pkg_cnt) + new_arsc[12:]
        return bytes(new_arsc)
    except Exception as e:
        print(f"Error patching ARSC: {e}")
        return arsc_data

def patch_axml_strings(data, replacements, new_version_code=None):
    try:
        pos = 8
        stype, ssize, scsize, scount, style_cnt, flags, sstart, styles_start = struct.unpack_from('<HHIIIIII', data, pos)
        offsets = list(struct.unpack_from(f'<{scount}I', data, pos + ssize))
        is_utf8 = (flags & (1 << 8)) != 0
        strings = []
        for off in offsets:
            sdata = data[pos + sstart + off:]
            if is_utf8:
                idx = 0
                if sdata[idx] & 0x80: idx += 2
                else: idx += 1
                if sdata[idx] & 0x80: idx += 2
                else: idx += 1
                end = sdata.find(b'\x00', idx)
                s = sdata[idx:end].decode('utf-8', errors='ignore')
            else:
                length = struct.unpack_from('<H', sdata, 0)[0]
                s = sdata[2:2+length*2].decode('utf-16le', errors='ignore')
            strings.append(s)

        for i in range(len(strings)):
            for old_txt, new_txt in replacements.items():
                if old_txt in strings[i]:
                    strings[i] = strings[i].replace(old_txt, new_txt)

        new_strings_data = bytearray()
        new_offsets = []
        for s in strings:
            new_offsets.append(len(new_strings_data))
            if is_utf8:
                encoded = s.encode('utf-8')
                char_len = len(s)
                byte_len = len(encoded)
                buf = bytearray()
                if char_len > 127:
                    buf.append(((char_len >> 8) & 0x7f) | 0x80)
                    buf.append(char_len & 0xff)
                else:
                    buf.append(char_len)
                if byte_len > 127:
                    buf.append(((byte_len >> 8) & 0x7f) | 0x80)
                    buf.append(byte_len & 0xff)
                else:
                    buf.append(byte_len)
                buf.extend(encoded)
                buf.append(0)
                new_strings_data.extend(buf)
            else:
                encoded = s.encode('utf-16le')
                char_len = len(s)
                new_strings_data.extend(struct.pack('<H', char_len))
                new_strings_data.extend(encoded)
                new_strings_data.extend(b'\x00\x00')

        pad = (4 - (len(new_strings_data) % 4)) % 4
        new_strings_data.extend(b'\x00' * pad)

        new_sstart = ssize + (scount * 4) + (style_cnt * 4)
        new_sstart_pad = (4 - (new_sstart % 4)) % 4
        new_sstart += new_sstart_pad
        new_scsize = new_sstart + len(new_strings_data)

        new_header = struct.pack('<HHIIIIII', stype, ssize, new_scsize, scount, style_cnt, flags, new_sstart, 0)
        new_offsets_bytes = struct.pack(f'<{scount}I', *new_offsets)
        new_pool = new_header + new_offsets_bytes + (b'\x00' * new_sstart_pad) + new_strings_data

        remainder = bytearray(data[pos + scsize:])
        if new_version_code is not None:
            for i in range(0, len(remainder) - 20, 4):
                aname = struct.unpack_from('<I', remainder, i + 4)[0]
                if aname == 27:
                    struct.pack_into('<I', remainder, i + 16, new_version_code)
                    print(f"Updated AXML versionCode to {new_version_code}")
                    break

        result = bytearray(data[:pos]) + new_pool + remainder
        struct.pack_into('<I', result, 4, len(result))
        return bytes(result)
    except Exception as e:
        print(f"Error patching AXML: {e}")
        return data

def main():
    root = "decompiled"
    if not os.path.exists(root):
        print(f"Directory {root} does not exist!")
        sys.exit(1)

    print("=== Patching ExteraLight (Zero-Crash Mode) ===")

    # 1. Update apktool.yml
    apktool_yml = os.path.join(root, "apktool.yml")
    if os.path.exists(apktool_yml):
        with open(apktool_yml, "r", encoding="utf-8") as f:
            yml = f.read()
        yml = re.sub(r"versionCode:\s*'?\d+'?", "versionCode: 72600", yml)
        yml = re.sub(r"versionName:\s*'?[^\'\n]+'?", "versionName: '2.0.1'", yml)
        with open(apktool_yml, "w", encoding="utf-8") as f:
            f.write(yml)
        print("Updated apktool.yml: versionCode 72600, versionName 2.0.1")

    # 2. Patch AndroidManifest.xml (handles text or binary)
    manifest_path = os.path.join(root, "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "rb") as f:
            m_data = f.read()

        if m_data.startswith(b"<?xml") or b"<manifest" in m_data[:200]:
            # Plain text XML
            text = m_data.decode("utf-8", errors="ignore")
            text = re.sub(r'android:versionCode="[^"]*"', 'android:versionCode="72600"', text)
            text = re.sub(r'android:versionName="[^"]*"', 'android:versionName="2.0.1"', text)
            text = re.sub(r'android:label="Nekogram"', 'android:label="ExteraLight"', text)
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(text)
            print("Patched text AndroidManifest.xml")
        else:
            # Binary XML
            new_m = patch_axml_strings(m_data, {"13.1.1": "2.0.1", "Nekogram": "ExteraLight"}, new_version_code=72600)
            with open(manifest_path, "wb") as f:
                f.write(new_m)
            print("Patched binary AndroidManifest.xml")

    # 3. Patch resources.arsc
    arsc_path = os.path.join(root, "resources.arsc")
    if os.path.exists(arsc_path):
        with open(arsc_path, "rb") as f:
            arsc_data = f.read()
        replacements = {
            "Nekogram Beta": "ExteraLight",
            "Nekogram": "ExteraLight",
            "nekogram": "exteralight",
            "Некограм": "ExteraLight",
            "некограм": "exteralight"
        }
        new_arsc = patch_arsc_strings(arsc_data, replacements)
        with open(arsc_path, "wb") as f:
            f.write(new_arsc)
        print("Successfully patched resources.arsc!")

    # 4. Patch Neko Cat vector drawables (PFi.xml and Egm.xml)
    plane_path = "M43.5,62 C39,58 34,52 34,43 C34,32 43,23 54,23 C65,23 74,32 74,43 C74,52 69,58 64.5,62 L64.5,67 C64.5,68 63.5,69 62.5,69 L45.5,69 C44.5,69 43.5,68 43.5,67 Z M66.5,35.5 L41.5,45.2 C39.9,45.8 40,47.8 41.6,48.3 L48,50.4 L62,41.2 C62.6,40.8 63.3,41.6 62.7,42.1 L51.2,52.8 L50.6,57.2 C50.6,58.2 51.8,58.7 52.4,58 L55.9,54.5 L61.3,58.5 C62.3,59.2 63.7,58.7 63.9,57.5 L68.3,37.2 C68.6,35.8 67.3,35.1 66.5,35.5 Z"
    for cat_res in ["res/PFi.xml", "res/Egm.xml"]:
        p = os.path.join(root, cat_res)
        if os.path.exists(p):
            with open(p, "rb") as f:
                cdata = f.read()
            if b"513.8,348.07" in cdata:
                new_cdata = patch_axml_strings(cdata, {"M513.8,348.07": plane_path})
                with open(p, "wb") as f:
                    f.write(new_cdata)
                print(f"Replaced cat vector in {cat_res} with Lightbulb+Plane")

    # 5. Generate and replace launcher icon PNGs
    res_dir = os.path.join(root, "res")
    if os.path.exists(res_dir):
        icon_renders = [
            ("icon_app.svg", "res/9wU.png", 48, 48),
            ("icon_app.svg", "res/ynk.png", 72, 72),
            ("icon_app.svg", "res/FSV.png", 96, 96),
            ("icon_app.svg", "res/RJS.png", 144, 144),
            ("icon_app.svg", "res/o-_.png", 192, 192),
            ("icon_fg.svg", "res/bBP.png", 108, 108),
            ("icon_fg.svg", "res/yi4.png", 162, 162),
            ("icon_fg.svg", "res/tPr.png", 216, 216),
            ("icon_fg.svg", "res/BME.png", 324, 324),
        ]
        for svg, dest_rel, w, h in icon_renders:
            dest = os.path.join(root, dest_rel)
            if os.path.exists(svg) and os.path.exists(os.path.dirname(dest)):
                try:
                    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), svg, "-o", dest], check=True)
                    print(f"Rendered {svg} -> {dest_rel} ({w}x{h})")
                except Exception as e:
                    print(f"rsvg-convert skipped for {dest_rel}: {e}")

    # 6. Smali patching: Easter Egg and Branding
    smali_dirs = [os.path.join(root, d) for d in os.listdir(root) if d.startswith("smali")]
    print(f"Scanning smali directories: {smali_dirs}")

    shrug_patterns = [
        "¯\\_(ツ)_/¯",
        "\\u00af\\_(\\u30c4)_/\\u00af",
        "¯\\_(^)_/¯",
        "\\u00af\\_(^)_/\\u00af"
    ]
    easter_egg_text = "Мур мяу!!"

    egg_count = 0
    brand_count = 0

    for sdir in smali_dirs:
        for r, _, files in os.walk(sdir):
            for file in files:
                if not file.endswith(".smali"):
                    continue
                filepath = os.path.join(r, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    mod = False
                    for pat in shrug_patterns:
                        if pat in content:
                            content = content.replace(pat, easter_egg_text)
                            mod = True
                            egg_count += 1
                            print(f"Patched easter egg in {file}")

                    # Replace UI titles and branding strings (excluding internal Ltw/nekomimi package references)
                    if '"Nekogram"' in content:
                        content = content.replace('"Nekogram"', '"ExteraLight"')
                        mod = True
                        brand_count += 1
                    if '"Neko Settings"' in content:
                        content = content.replace('"Neko Settings"', '"ExteraLight Settings"')
                        mod = True
                        brand_count += 1
                    if '"Настройки Neko"' in content:
                        content = content.replace('"Настройки Neko"', '"Настройки ExteraLight"')
                        mod = True
                        brand_count += 1
                    if '⚡ ExteraLight Super Profile' in content:
                        content = content.replace('⚡ ExteraLight Super Profile', '')
                        mod = True

                    if mod:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                except Exception as e:
                    pass

    print(f"Smali patches completed: {egg_count} easter egg occurrences, {brand_count} branding strings")
    print("=== Patching finished successfully! ===")

if __name__ == "__main__":
    main()

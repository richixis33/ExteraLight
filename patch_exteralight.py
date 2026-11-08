import os
import re
import sys

def main():
    root = "decompiled"
    if not os.path.exists(root):
        print("Decompiled folder not found!")
        sys.exit(1)

    print("=== Patching ExteraLight ===")

    # 1. Update apktool.yml versionCode & versionName
    apktool_yml = os.path.join(root, "apktool.yml")
    if os.path.exists(apktool_yml):
        with open(apktool_yml, "r", encoding="utf-8") as f:
            yml = f.read()
        yml = re.sub(r"versionCode:\s*'?\d+'?", "versionCode: '7250'", yml)
        yml = re.sub(r"versionName:\s*'?[^\'\n]+'?", "versionName: '2.0.0 (ExteraLight)'", yml)
        with open(apktool_yml, "w", encoding="utf-8") as f:
            f.write(yml)
        print("Updated apktool.yml: versionCode 7250, versionName 2.0.0")

    # 2. Patch strings.xml across all values-* directories
    string_files = []
    res_dir = os.path.join(root, "res")
    if os.path.exists(res_dir):
        for d in os.listdir(res_dir):
            if d.startswith("values"):
                s_file = os.path.join(res_dir, d, "strings.xml")
                if os.path.exists(s_file):
                    string_files.append(s_file)

        print(f"Found {len(string_files)} strings.xml files")
        for sf in string_files:
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    content = f.read()

                content = content.replace("Nekogram", "ExteraLight")
                content = content.replace("некограм", "ExteraLight")
                content = content.replace("Некограм", "ExteraLight")

                with open(sf, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"Error patching {sf}: {e}")

    # 3. Patch Icons: Replace launcher foreground and logo with Lightbulb + Telegram plane
    icon_vector = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <!-- Glow rays -->
    <path
        android:fillColor="#00000000"
        android:strokeColor="#B3FFFFFF"
        android:strokeWidth="2.5"
        android:strokeLineCap="round"
        android:pathData="M54,15 L54,20 M77,24.5 L73.5,28 M87,44 L82,44 M31,24.5 L34.5,28 M21,44 L26,44" />
    <!-- Bulb Glass Outline -->
    <path
        android:fillColor="#00000000"
        android:strokeColor="#E6FFFFFF"
        android:strokeWidth="2.8"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:pathData="M43.5,62 C39,58 34,52 34,43 C34,32 43,23 54,23 C65,23 74,32 74,43 C74,52 69,58 64.5,62 L64.5,67 C64.5,68 63.5,69 62.5,69 L45.5,69 C44.5,69 43.5,68 43.5,67 Z" />
    <!-- Screw Base Threads -->
    <path
        android:fillColor="#CCFFFFFF"
        android:pathData="M45,71 C45,70.5 45.5,70 46,70 L62,70 C62.5,70 63,70.5 63,71 L62,73 L46,73 Z" />
    <path
        android:fillColor="#B3FFFFFF"
        android:pathData="M46.5,74.5 C46.5,74 47,73.5 47.5,73.5 L60.5,73.5 C61,73.5 61.5,74 61.5,74.5 L60,76.5 C59.5,78 57,79 54,79 C51,79 48.5,78 48,76.5 Z" />
    <!-- Telegram Paper Plane -->
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M66.5,35.5 L41.5,45.2 C39.9,45.8 40,47.8 41.6,48.3 L48,50.4 L62,41.2 C62.6,40.8 63.3,41.6 62.7,42.1 L51.2,52.8 L50.6,57.2 C50.6,58.2 51.8,58.7 52.4,58 L55.9,54.5 L61.3,58.5 C62.3,59.2 63.7,58.7 63.9,57.5 L68.3,37.2 C68.6,35.8 67.3,35.1 66.5,35.5 Z" />
</vector>
"""

    if os.path.exists(res_dir):
        icon_paths = [
            os.path.join(res_dir, "drawable", "ic_foreground.xml"),
            os.path.join(res_dir, "drawable", "ic_monochrome.xml"),
            os.path.join(res_dir, "drawable", "ic_foreground_white.xml"),
            os.path.join(res_dir, "drawable", "ic_logo_foreground.xml"),
            os.path.join(res_dir, "drawable-v31", "ic_foreground_monet.xml")
        ]
        for ip in icon_paths:
            os.makedirs(os.path.dirname(ip), exist_ok=True)
            with open(ip, "w", encoding="utf-8") as f:
                f.write(icon_vector)
            print(f"Updated icon: {ip}")

    # 4. Patch Easter Egg: Replace shrug with 'Мур мяу!!' in all smali files
    smali_dirs = [os.path.join(root, d) for d in os.listdir(root) if d.startswith("smali")]
    shrug_target = "¯\\_(ツ)_/¯"
    shrug_replacement = "Мур мяу!!"
    count_patched = 0

    for sdir in smali_dirs:
        for r, _, files in os.walk(sdir):
            for file in files:
                if file.endswith(".smali"):
                    filepath = os.path.join(r, file)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            s_content = f.read()
                        if shrug_target in s_content or "¯\\_(ツ)_/¯" in s_content:
                            s_content = s_content.replace(shrug_target, shrug_replacement)
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(s_content)
                            count_patched += 1
                            print(f"Patched easter egg in: {file}")
                    except Exception as e:
                        pass

    print(f"Total smali files patched for easter egg: {count_patched}")
    print("=== Patching complete! ===")

if __name__ == "__main__":
    main()

import os
import sys
import re
import platform
import subprocess
import urllib.request
import zipfile
from pathlib import Path

AURORA_PIXEL_TEMPLATE = """[default]
UserReadableName=Google Pixel 7a
Build.BOOTLOADER=lynx-1.0-9716681
Build.BRAND=google
Build.DEVICE=lynx
Build.FINGERPRINT=google/lynx/lynx:13/TQ2B.230505.005.A1/9808202:user/release-keys
Build.HARDWARE=lynx
Build.ID=TQ2A.230505.002
Build.MANUFACTURER=Google
Build.MODEL=Pixel 7a
Build.PRODUCT=lynx
Build.RADIO=g5300n-230203-230323-B-9801058,g5300n-230203-230323-B-9801058
Build.VERSION.RELEASE=13
Build.VERSION.SDK_INT=33
CellOperator=310
Client=android-google
Features=android.hardware.sensor.proximity,android.hardware.telephony.ims.singlereg,android.hardware.sensor.accelerometer,android.software.controls,android.hardware.faketouch,android.software.telecom,android.hardware.telephony.subscription,android.hardware.telephony.euicc,android.hardware.usb.accessory,android.hardware.telephony.data,android.hardware.sensor.dynamic.head_tracker,android.software.backup,android.hardware.touchscreen,android.hardware.touchscreen.multitouch,android.software.erofs,android.software.print,android.software.activities_on_secondary_displays,android.hardware.wifi.rtt,com.google.android.feature.PIXEL_2017_EXPERIENCE,android.software.voice_recognizers,android.software.picture_in_picture,android.hardware.fingerprint,android.hardware.sensor.gyroscope,android.hardware.audio.low_latency,android.software.vulkan.deqp.level,android.software.cant_save_state,com.google.android.feature.PIXEL_2018_EXPERIENCE,android.hardware.security.model.compatible,android.hardware.telephony.messaging,com.google.android.feature.PIXEL_2019_EXPERIENCE,android.hardware.telephony.calling,android.hardware.opengles.aep,org.lineageos.livedisplay,android.hardware.bluetooth,android.software.window_magnification,android.hardware.telephony.radio.access,android.hardware.camera.autofocus,android.hardware.telephony.gsm,android.hardware.telephony.ims,android.software.incremental_delivery,android.hardware.se.omapi.ese,android.software.opengles.deqp.level,vendor.android.hardware.camera.preview-dis.front,com.google.android.feature.PIXEL_2022_MIDYEAR_EXPERIENCE,android.hardware.camera.concurrent,android.hardware.usb.host,android.hardware.audio.output,android.software.verified_boot,android.hardware.camera.flash,android.hardware.camera.front,android.hardware.sensor.hifi_sensors,android.hardware.se.omapi.uicc,android.hardware.strongbox_keystore,android.hardware.screen.portrait,android.hardware.nfc,com.nxp.mifare,com.google.android.feature.PIXEL_2021_MIDYEAR_EXPERIENCE,android.hardware.sensor.stepdetector,android.software.home_screen,android.hardware.context_hub,vendor.android.hardware.camera.preview-dis.back,android.hardware.microphone,android.software.autofill,org.lineageos.hardware,org.lineageos.globalactions,android.software.securely_removes_users,com.google.android.feature.PIXEL_EXPERIENCE,android.hardware.bluetooth_le,android.hardware.sensor.compass,android.hardware.touchscreen.multitouch.jazzhand,android.hardware.sensor.barometer,android.software.app_widgets,com.google.android.feature.PIXEL_2020_MIDYEAR_EXPERIENCE,android.hardware.telephony.carrierlock,android.software.input_methods,android.hardware.sensor.light,android.hardware.vulkan.version,android.software.companion_device_setup,android.software.device_admin,android.hardware.wifi.passpoint,android.hardware.camera,org.lineageos.trust,android.hardware.device_unique_attestation,android.hardware.screen.landscape,android.software.device_id_attestation,android.hardware.ram.normal,com.google.android.feature.PIXEL_2019_MIDYEAR_EXPERIENCE,android.software.managed_users,android.software.webview,android.hardware.sensor.stepcounter,android.hardware.camera.capability.manual_post_processing,android.hardware.camera.any,android.hardware.camera.capability.raw,android.hardware.vulkan.compute,android.hardware.touchscreen.multitouch.distinct,android.hardware.location.network,android.software.cts,android.hardware.camera.capability.manual_sensor,android.software.app_enumeration,android.hardware.camera.level.full,android.hardware.identity_credential,android.hardware.wifi.direct,android.software.live_wallpaper,com.google.android.feature.GOOGLE_EXPERIENCE,android.software.ipsec_tunnels,org.lineageos.settings,android.hardware.audio.pro,android.hardware.nfc.hcef,android.hardware.location.gps,android.software.midi,android.hardware.nfc.any,android.hardware.nfc.ese,android.hardware.nfc.hce,android.hardware.hardware_keystore,com.google.android.feature.PIXEL_2020_EXPERIENCE,android.hardware.telephony.euicc.mep,android.hardware.wifi,android.hardware.location,android.hardware.vulkan.level,com.google.android.feature.PIXEL_2021_EXPERIENCE,android.hardware.keystore.app_attest_key,android.hardware.wifi.aware,com.google.android.feature.PIXEL_2022_EXPERIENCE,android.software.secure_lock_screen,android.hardware.telephony,android.software.file_based_encryption
GL.Extensions=GL_ANDROID_extension_pack_es31a,GL_ARM_mali_program_binary,GL_ARM_mali_shader_binary,GL_ARM_rgba8,GL_ARM_shader_framebuffer_fetch,GL_ARM_shader_framebuffer_fetch_depth_stencil,GL_ARM_texture_unnormalized_coordinates,GL_EXT_EGL_image_array,GL_EXT_YUV_target,GL_EXT_blend_minmax,GL_EXT_buffer_storage,GL_EXT_clip_control,GL_EXT_color_buffer_float,GL_EXT_color_buffer_half_float,GL_EXT_copy_image,GL_EXT_debug_marker,GL_EXT_discard_framebuffer,GL_EXT_disjoint_timer_query,GL_EXT_draw_buffers_indexed,GL_EXT_draw_elements_base_vertex,GL_EXT_external_buffer,GL_EXT_float_blend,GL_EXT_geometry_shader,GL_EXT_gpu_shader5,GL_EXT_multisampled_render_to_texture,GL_EXT_multisampled_render_to_texture2,GL_EXT_occlusion_query_boolean,GL_EXT_primitive_bounding_box,GL_EXT_protected_textures,GL_EXT_read_format_bgra,GL_EXT_robustness,GL_EXT_sRGB,GL_EXT_sRGB_write_control,GL_EXT_shader_framebuffer_fetch,GL_EXT_shader_io_blocks,GL_EXT_shader_non_constant_global_initializers,GL_EXT_shader_pixel_local_storage,GL_EXT_shadow_samplers,GL_EXT_tessellation_shader,GL_EXT_texture_border_clamp,GL_EXT_texture_buffer,GL_EXT_texture_compression_astc_decode_mode,GL_EXT_texture_compression_astc_decode_mode_rgb9e5,GL_EXT_texture_cube_map_array,GL_EXT_texture_filter_anisotropic,GL_EXT_texture_format_BGRA8888,GL_EXT_texture_rg,GL_EXT_texture_sRGB_R8,GL_EXT_texture_sRGB_RG8,GL_EXT_texture_sRGB_decode,GL_EXT_texture_storage,GL_EXT_texture_type_2_10_10_10_REV,GL_EXT_unpack_subimage,GL_KHR_blend_equation_advanced,GL_KHR_blend_equation_advanced_coherent,GL_KHR_debug,GL_KHR_robust_buffer_access_behavior,GL_KHR_robustness,GL_KHR_texture_compression_astc_hdr,GL_KHR_texture_compression_astc_ldr,GL_KHR_texture_compression_astc_sliced_3d,GL_OES_EGL_image,GL_OES_EGL_image_external,GL_OES_EGL_image_external_essl3,GL_OES_EGL_sync,GL_OES_blend_equation_separate,GL_OES_blend_func_separate,GL_OES_blend_subtract,GL_OES_byte_coordinates,GL_OES_compressed_ETC1_RGB8_texture,GL_OES_compressed_paletted_texture,GL_OES_copy_image,GL_OES_depth24,GL_OES_depth_texture,GL_OES_depth_texture_cube_map,GL_OES_draw_buffers_indexed,GL_OES_draw_elements_base_vertex,GL_OES_draw_texture,GL_OES_element_index_uint,GL_OES_extended_matrix_palette,GL_OES_fbo_render_mipmap,GL_OES_fixed_point,GL_OES_framebuffer_object,GL_OES_geometry_shader,GL_OES_get_program_binary,GL_OES_gpu_shader5,GL_OES_mapbuffer,GL_OES_matrix_get,GL_OES_matrix_palette,GL_OES_packed_depth_stencil,GL_OES_point_size_array,GL_OES_point_sprite,GL_OES_primitive_bounding_box,GL_OES_query_matrix,GL_OES_read_format,GL_OES_required_internalformat,GL_OES_rgb8_rgba8,GL_OES_sample_shading,GL_OES_sample_variables,GL_OES_shader_image_atomic,GL_OES_shader_io_blocks,GL_OES_shader_multisample_interpolation,GL_OES_single_precision,GL_OES_standard_derivatives,GL_OES_stencil8,GL_OES_stencil_wrap,GL_OES_surfaceless_context,GL_OES_tessellation_shader,GL_OES_texture_3D,GL_OES_texture_border_clamp,GL_OES_texture_buffer,GL_OES_texture_compression_astc,GL_OES_texture_cube_map,GL_OES_texture_cube_map_array,GL_OES_texture_float_linear,GL_OES_texture_mirrored_repeat,GL_OES_texture_npot,GL_OES_texture_stencil8,GL_OES_texture_storage_multisample_2d_array,GL_OES_vertex_array_object,GL_OES_vertex_half_float,GL_OVR_multiview,GL_OVR_multiview2,GL_OVR_multiview_multisampled_render_to_texture
GL.Version=196610
GSF.version=203615037
HasFiveWayNavigation=false
HasHardKeyboard=false
Keyboard=1
Locales=af,am,ar,as,az,be,bg,bn,bs,ca,cs,da,de,el,en,es,et,eu,fa,fi,fil,fr,gu,he,hi,hr,hu,hy,id,is,it,iw,ja,ka,kk,km,kn,ko,ky,lo,lt,lv,mk,ml,mn,mr,ms,my,nb,ne,nl,or,pa,pl,pt,ro,ru,si,sk,sl,sq,sr,sv,sw,ta,te,th,tr,uk,ur,uz,vi,zh,zu
Navigation=1
Platforms=arm64-v8a
Roaming=mobile-notroaming
Screen.Density=420
Screen.Height=2156
Screen.Width=1080
ScreenLayout=2
SharedLibraries=android.test.base,android.test.mock,android.hidl.manager-V1.0-java,google-ril,libedgetpu_client.google.so,libedgetpu_util.so,android.hidl.base-V1.0-java,com.google.android.camera.experimental2022,libOpenCL-pixel.so,com.android.location.provider,oemrilhook,android.net.ipsec.ike,com.android.future.usb.accessory,android.ext.shared,javax.obex,com.google.android.gms,lib_aion_buffer.so,libgxp.so,gxp_metrics_logger.so,android.test.runner,org.apache.http.legacy,com.android.cts.ctsshim.shared_library,com.android.nfc_extras,com.android.media.remotedisplay,com.android.mediadrm.signer,android.system.virtualmachine
SimOperator=38
TimeZone=UTC-10
TouchScreen=3
Vending.version=82201710
Vending.versionString=22.0.17-21 [0] [PR] 332555730
"""

class LocalFileResponse:
    def __init__(self, filepath, url):
        self.filepath = filepath
        self.status_code = 200
        self.url = url
        filename = os.path.basename(filepath)
        content_type = "application/vnd.android.package-archive" if filename.endswith(".apk") else "application/octet-stream"
        self.headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"'
        }

    def iter_content(self, chunk_size=8192):
        with open(self.filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def close(self):
        pass


class ApkeepScraper:
    def __init__(self, source_instance):
        self.source = source_instance

    def get(self, url, stream=False, headers=None, allow_redirects=True):
        if url.startswith("apkeep_local:"):
            filepath = url.split("apkeep_local:")[1]
            return LocalFileResponse(filepath, url)
        
        elif url.startswith("apkeep_dl:"):
            package_name = url.split("apkeep_dl:")[1]
            out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
            xapk_path = self.source._download_universal_xapk(package_name, out_dir)
            return LocalFileResponse(xapk_path, url)
        else:
            raise ValueError(f"Unknown URL format: {url}")


class ApkeepSource:
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.google_email = os.getenv("GOOGLE_EMAIL", "").strip()
        self.aas_token = os.getenv("AAS_TOKEN", "").strip()

        if not self.google_email or not self.aas_token:
            raise ValueError("Missing GOOGLE_EMAIL or AAS_TOKEN environment variables!")

        self.bin_path = self._ensure_binary_exists()
        self.scraper = ApkeepScraper(self)

    def _ensure_binary_exists(self) -> str:
        bin_dir = os.path.join(os.getcwd(), "core", "bin")
        os.makedirs(bin_dir, exist_ok=True)
        is_win = platform.system() == "Windows"
        bin_name = "apkeep.exe" if is_win else "apkeep"
        bin_path = os.path.join(bin_dir, bin_name)

        if os.path.exists(bin_path):
            return bin_path

        print(f"[*] [apkeep] Downloading apkeep tool for {platform.system()}...")
        url = "https://github.com/EFForg/apkeep/releases/latest/download/apkeep-x86_64-pc-windows-msvc.exe" if is_win else "https://github.com/EFForg/apkeep/releases/latest/download/apkeep-x86_64-unknown-linux-gnu"
        try:
            urllib.request.urlretrieve(url, bin_path)
            if not is_win:
                os.chmod(bin_path, 0o755)
        except Exception as e:
            raise RuntimeError(f"Failed to download apkeep: {e}")
        return bin_path

    def _download_universal_xapk(self, package_name: str, out_dir: str) -> str:
        os.makedirs(out_dir, exist_ok=True)
        dir_64 = os.path.join(out_dir, "64")
        dir_32 = os.path.join(out_dir, "32")
        os.makedirs(dir_64, exist_ok=True)
        os.makedirs(dir_32, exist_ok=True)

        prop_64 = os.path.abspath(os.path.join(out_dir, "64.properties"))
        with open(prop_64, "w", encoding="utf-8") as f:
            f.write(AURORA_PIXEL_TEMPLATE)

        prop_32 = os.path.abspath(os.path.join(out_dir, "32.properties"))
        with open(prop_32, "w", encoding="utf-8") as f:
            f.write(AURORA_PIXEL_TEMPLATE.replace("Platforms=arm64-v8a", "Platforms=armeabi-v7a,armeabi"))

        print(f"[*] [apkeep] Downloading 64-bit splits (he/en) for {package_name}...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"locale=he_IL,split_apk=true,device=default,device_properties_file={prop_64}",
            "--accept-tos", dir_64
        ], check=True, stdout=subprocess.DEVNULL)

        print(f"[*] [apkeep] Downloading 32-bit splits (he/en) for {package_name}...")
        subprocess.run([
            self.bin_path, "-a", package_name, "-d", "google-play",
            "-e", self.google_email, "-t", self.aas_token,
            "-o", f"locale=he_IL,split_apk=true,device=default,device_properties_file={prop_32}",
            "--accept-tos", dir_32
        ], check=True, stdout=subprocess.DEVNULL)

        all_apks = {}
        for d in [dir_64, dir_32]:
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".apk"):
                        all_apks[f] = os.path.join(root, f)

        if not all_apks:
            raise RuntimeError("No APK splits found after download.")

        xapk_path = os.path.join(out_dir, f"{package_name}_universal.xapk")
        with zipfile.ZipFile(xapk_path, 'w') as z:
            z.writestr("manifest.json", f'{{"package_name":"{package_name}"}}')
            for apk_name, apk_path in all_apks.items():
                z.write(apk_path, apk_name)

        return xapk_path

    def get_latest_version(self, package_name: str):
        print(f"[*] [apkeep] Checking Play Store web page for {package_name}...")
        url = f"https://play.google.com/store/apps/details?id={package_name}&hl=en"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            
            version_match = re.search(r'\[\[\["(\d+(?:\.\d+)+)"\]\]', html)
            if not version_match:
                version_match = re.search(r'\["(\d+\.\d+\.\d+(?:\.\d+)?)"\]', html)
            if version_match:
                version = version_match.group(1)
                print(f"[+] [apkeep] Found Google Play version: {version}")
                return version, f"dl:{package_name}", package_name
        except Exception as e:
            print(f"[-] [apkeep] Web scrape failed: {e}")

        print(f"[!] [apkeep] Version hidden. Extracting from Universal build...")
        out_dir = os.path.join(os.getcwd(), "scratch", "apkeep_tmp")
        try:
            xapk_path = self._download_universal_xapk(package_name, out_dir)
        except Exception as e:
            print(f"[-] [apkeep] Download failed: {e}")
            return None, None, None

        decode_dir = os.path.join(out_dir, f"{package_name}_meta")
        os.makedirs(decode_dir, exist_ok=True)
        base_apk_path = os.path.join(decode_dir, "base.apk")
        
        version = "latest"
        try:
            # 1. חילוץ קובץ הבסיס (Base APK) מתוך ה-XAPK
            with zipfile.ZipFile(xapk_path, 'r') as z:
                # מחפשים את קובץ ה-APK שאין לו את המילה config בשם
                base_apk_name = next((n for n in z.namelist() if n.endswith(".apk") and "config" not in n), None)
                if base_apk_name:
                    with open(base_apk_path, 'wb') as f:
                        f.write(z.read(base_apk_name))
                else:
                    raise FileNotFoundError("Base APK not found inside XAPK")

            # 2. הפעלת apktool על קובץ הבסיס בלבד!
            apktool_cmd = ["apktool", "d", "-s", "-f", "-o", os.path.join(decode_dir, "decoded"), base_apk_path]
            subprocess.run(apktool_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            yml_path = os.path.join(decode_dir, "decoded", "apktool.yml")
            if os.path.exists(yml_path):
                with open(yml_path, "r", encoding="utf-8") as f:
                    match = re.search(r"versionName:\s*['\"]?([^'\">\r\n]+)", f.read())
                    if match:
                        version = match.group(1).strip()
            print(f"[+] [apkeep] Real Google Play Version extracted: {version}")
        except Exception as e:
            print(f"[-] [apkeep] Failed to extract exact version: {e}")

        return version, f"local:{xapk_path}", package_name

    def get_download_url(self, release_url: str):
        if release_url.startswith("local:"):
            return f"apkeep_local:{release_url.split('local:')[1]}"
        elif release_url.startswith("dl:"):
            return f"apkeep_dl:{release_url.split('dl:')[1]}"
        return None

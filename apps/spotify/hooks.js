// Spotify Kosher Media Tweaks Hook Module
Java.perform(function () {
    console.log("[*] [Frida] Injecting Spotify Media Hooks...");

    // 1. Null image data loader
    try {
        var EsImageData = Java.use("com.spotify.image.esperanto.proto.EsImage$ImageData");
        if (EsImageData.getData) {
            EsImageData.getData.implementation = function () {
                return null;
            };
            console.log("[+] [Frida] Spotify EsImage$ImageData.getData() hooked -> null");
        }
    } catch (e) {}

    // 2. Null video surface texture view
    try {
        var VideoSurface = Java.use("com.spotify.betamax.player.VideoSurfaceView");
        if (VideoSurface.getTextureView) {
            VideoSurface.getTextureView.implementation = function () {
                return null;
            };
            console.log("[+] [Frida] Spotify VideoSurfaceView.getTextureView() hooked -> null");
        }
    } catch (e) {}
});

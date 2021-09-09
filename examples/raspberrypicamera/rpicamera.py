import asyncio
import json
import logging
import os
from collections import OrderedDict

import picamera
from aiohttp import web
from aiortc import RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.mediastreams import AudioStreamTrack, VideoStreamTrack
from aiortc.rtcrtpparameters import RTCRtpCodecCapability
from pitrack import H264EncodedStreamTrack
from rtcpeerconnection import RTCPeerConnection
from rtcrtpsender import RTCRtpSender

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FRAME_RATE = 30
CAMERA_RESOLUTION = (640, 480)
BASE_PATH = os.path.dirname(__file__)

audio = None
camera = None
video_track = None

codec_parameters = OrderedDict(
    [
        ("packetization-mode", "1"),
        ("level-asymmetry-allowed", "1"),
        ("profile-level-id", "42001f"),
    ]
)
pi_capability = RTCRtpCodecCapability(
    mimeType="video/H264", clockRate=90000, channels=None, parameters=codec_parameters
)
preferences = [pi_capability]
pcs = set()


async def index(request):
    content = open(os.path.join(BASE_PATH, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(BASE_PATH, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    global audio, camera, video_track
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    
    if not video_track:
        video_track = H264EncodedStreamTrack(FRAME_RATE)

    if not camera:
        camera = picamera.PiCamera()
        camera.resolution = CAMERA_RESOLUTION
        camera.framerate = FRAME_RATE

        camera.start_recording(
            video_track,
            format="h264",
            profile="constrained",
            inline_headers=True,
            sei=False,
        )

    # Read audio stream from `hw:1,0` (via alsa, from card1, device0. see output from `arecord -l`)
    # Please check default Capture volume by `amixer`. You can set Capture volume by `amixer sset 'Capture' 80%`
    if not audio:
        try:
            audio = MediaPlayer(
                "hw:1,0", format="alsa", options={"channels": "1", "sample_rate": "44100"}
            )
        except:
            print("Could not open or read audio device.")
            audio = None

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s" % pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    await pc.setRemoteDescription(offer)
    for t in pc.getTransceivers():
        if t.kind == "audio" and audio and audio.audio:
            audio_relay = MediaRelay()
            pc.addTrack(audio_relay.subscribe(audio.audio))
            # pc.addTrack(audio.audio)
        if t.kind == "video" and video_track:
            t.setCodecPreferences(preferences)
            video_relay = MediaRelay()
            pc.addTrack(video_relay.subscribe(video_track))
            # pc.addTrack(video_track)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    logger.info(answer)
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    global camera
    # close peer connections
    print("Shutting down")
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    camera.stop_recording()
    camera.close()
    audio.audio.stop()


if __name__ == "__main__":
    ssl_context = None
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host="0.0.0.0", port=8080, ssl_context=ssl_context)

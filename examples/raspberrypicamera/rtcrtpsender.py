from pitrack import EncodedStreamTrack, EncodedRelayStreamTrack

from aiortc.codecs import get_encoder
from aiortc.rtcrtpparameters import RTCRtpCodecParameters
from aiortc.rtcrtpsender import RTCRtpSender as OriginalRTCRtpSender


class RTCRtpSender(OriginalRTCRtpSender):
    async def _next_encoded_frame(self, codec: RTCRtpCodecParameters):
        print(self.__track)
        if isinstance(self.__track, EncodedStreamTrack) or isinstance(self.__track, EncodedRelayStreamTrack):
            force_keyframe = self.__force_keyframe
            self.__force_keyframe = False
            return await self.__track.recv_encoded(force_keyframe)
        else:
            frame = await self.__track.recv()
            if self.__encoder is None:
                self.__encoder = get_encoder(codec)
            force_keyframe = self.__force_keyframe
            self.__force_keyframe = False
            return await self.__loop.run_in_executor(
                None, self.__encoder.encode, frame, force_keyframe
            )

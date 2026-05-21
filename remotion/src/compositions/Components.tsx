import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Chapter {
  id: number;
  title: string;
  timestamp_start: string;
  narration: string;
  duration_seconds: number;
}

interface ScriptData {
  title: string;
  brand: { color_primary: string; channel_name: string };
  intro: { duration_seconds: number };
  chapters: Chapter[];
  outro: { duration_seconds: number };
}

// ─── Logo Intro (3 seconds) ───────────────────────────────────────────────────

export const IntroSequence: React.FC<{ channelName: string; primaryColor: string }> = ({
  channelName,
  primaryColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = spring({ frame, fps, config: { damping: 20 }, delay: 10 });
  const scale = interpolate(frame, [0, 30], [0.8, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: primaryColor, justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${scale})`, opacity, textAlign: "center" }}>
        {/* Logo image */}
        <Img
          src={staticFile("logo/logo.png")}
          style={{ width: 200, height: 200, objectFit: "contain" }}
        />
        <div
          style={{
            color: "white",
            fontFamily: "'Noto Sans Thai', sans-serif",
            fontSize: 32,
            marginTop: 20,
            letterSpacing: 4,
            fontWeight: 300,
          }}
        >
          {channelName}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Chapter Card (2 seconds) ─────────────────────────────────────────────────

export const ChapterCard: React.FC<{
  chapterNumber: number;
  title: string;
  primaryColor: string;
}> = ({ chapterNumber, title, primaryColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideIn = spring({ frame, fps, config: { damping: 25, stiffness: 200 } });
  const x = interpolate(slideIn, [0, 1], [-200, 0]);
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e", justifyContent: "center", alignItems: "flex-start" }}>
      {/* Accent bar */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: "50%",
          transform: "translateY(-50%)",
          width: 8,
          height: "30%",
          backgroundColor: primaryColor,
        }}
      />
      {/* Chapter content */}
      <div style={{ paddingLeft: 80, transform: `translateX(${x}px)`, opacity }}>
        <div
          style={{
            color: primaryColor,
            fontFamily: "'Noto Sans Thai', sans-serif",
            fontSize: 22,
            fontWeight: 400,
            textTransform: "uppercase",
            letterSpacing: 3,
            marginBottom: 12,
          }}
        >
          Chapter {chapterNumber}
        </div>
        <div
          style={{
            color: "white",
            fontFamily: "'Noto Sans Thai', sans-serif",
            fontSize: 52,
            fontWeight: 700,
            lineHeight: 1.3,
            maxWidth: 900,
          }}
        >
          {title}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Scene Slide (main content) ───────────────────────────────────────────────

export const SceneSlide: React.FC<{
  imageFile: string;
  audioFile: string;
  duration: number;
  chapterTitle: string;
  chapterIndex: number;
}> = ({ imageFile, audioFile, duration, chapterTitle, chapterIndex }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Ken Burns: gentle zoom over duration
  const totalFrames = duration * fps;
  const zoomScale = interpolate(frame, [0, totalFrames], [1.0, 1.06], {
    extrapolateRight: "clamp",
  });
  const panX = interpolate(frame, [0, totalFrames], [0, chapterIndex % 2 === 0 ? 20 : -20], {
    extrapolateRight: "clamp",
  });

  // Chapter badge fade
  const badgeOpacity = interpolate(frame, [0, 30, fps * 2, fps * 2.5], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      {/* Background image with Ken Burns */}
      <AbsoluteFill
        style={{
          overflow: "hidden",
          transform: `scale(${zoomScale}) translateX(${panX}px)`,
        }}
      >
        <Img
          src={staticFile(`images/${imageFile}`)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      {/* Subtle gradient overlay for text readability */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(to bottom, transparent 60%, rgba(0,0,0,0.45) 100%)",
        }}
      />

      {/* Chapter badge (fades out after 2.5 seconds) */}
      <div
        style={{
          position: "absolute",
          top: 40,
          right: 50,
          opacity: badgeOpacity,
          backgroundColor: "rgba(27,82,153,0.85)",
          borderRadius: 8,
          padding: "8px 18px",
          fontFamily: "'Noto Sans Thai', sans-serif",
          color: "white",
          fontSize: 22,
          fontWeight: 600,
          backdropFilter: "blur(4px)",
        }}
      >
        {chapterTitle}
      </div>

      {/* Audio */}
      {audioFile && (
        <Audio src={staticFile(`audio/${audioFile}`)} />
      )}
    </AbsoluteFill>
  );
};

// ─── Subtitle Overlay ─────────────────────────────────────────────────────────

export const SubtitleOverlay: React.FC<{
  text: string;
  opacity?: number;
}> = ({ text, opacity = 1 }) => (
  <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60 }}>
    <div
      style={{
        opacity,
        backgroundColor: "rgba(0,0,0,0.65)",
        borderRadius: 8,
        padding: "14px 32px",
        maxWidth: "85%",
        textAlign: "center",
        backdropFilter: "blur(6px)",
      }}
    >
      <span
        style={{
          color: "white",
          fontFamily: "'Noto Sans Thai', sans-serif",
          fontSize: 36,
          fontWeight: 500,
          lineHeight: 1.5,
          textShadow: "1px 1px 4px rgba(0,0,0,0.8)",
        }}
      >
        {text}
      </span>
    </div>
  </AbsoluteFill>
);

// ─── Outro ────────────────────────────────────────────────────────────────────

export const OutroSequence: React.FC<{
  primaryColor: string;
  channelName: string;
}> = ({ primaryColor, channelName }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const scale = spring({ frame, fps, config: { damping: 30 }, delay: 15 });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: primaryColor,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 30,
      }}
    >
      <Img
        src={staticFile("logo/logo.png")}
        style={{
          width: 160,
          height: 160,
          objectFit: "contain",
          opacity,
          transform: `scale(${scale})`,
        }}
      />
      <div
        style={{
          color: "white",
          fontFamily: "'Noto Sans Thai', sans-serif",
          fontSize: 42,
          fontWeight: 700,
          opacity,
        }}
      >
        {channelName}
      </div>
      <div
        style={{
          color: "rgba(255,255,255,0.75)",
          fontFamily: "'Noto Sans Thai', sans-serif",
          fontSize: 26,
          opacity,
          textAlign: "center",
        }}
      >
        กด Subscribe เพื่อไม่พลาดคลิปใหม่
      </div>
    </AbsoluteFill>
  );
};

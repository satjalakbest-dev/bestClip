import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import {
  ChapterCard,
  IntroSequence,
  OutroSequence,
  SceneSlide,
} from "./Components";

const FPS = 30;
const INTRO_FRAMES = 90;       // 3 seconds
const CHAPTER_CARD_FRAMES = 60; // 2 seconds
const OUTRO_FRAMES = 150;      // 5 seconds

interface ScriptData {
  title: string;
  brand: { color_primary: string; channel_name: string };
  intro: { duration_seconds: number; narration?: string };
  chapters: Array<{
    id: number;
    title: string;
    duration_seconds: number;
    narration: string;
  }>;
  outro: { duration_seconds: number };
}

export const BlueOclockVideo: React.FC<{ script: ScriptData }> = ({ script }) => {
  const { brand } = script;
  let currentFrame = 0;

  const sequences: React.ReactNode[] = [];

  // ── Intro
  sequences.push(
    <Sequence key="intro" from={0} durationInFrames={INTRO_FRAMES}>
      <IntroSequence
        channelName={brand.channel_name}
        primaryColor={brand.color_primary}
      />
      <Audio src={staticFile("audio/intro.mp3")} />
    </Sequence>
  );
  currentFrame += INTRO_FRAMES;

  // ── Chapters
  for (const ch of script.chapters) {
    const chapterFrames = Math.ceil(ch.duration_seconds * FPS);

    // Chapter card
    sequences.push(
      <Sequence
        key={`card_${ch.id}`}
        from={currentFrame}
        durationInFrames={CHAPTER_CARD_FRAMES}
      >
        <ChapterCard
          chapterNumber={ch.id}
          title={ch.title}
          primaryColor={brand.color_primary}
        />
      </Sequence>
    );
    currentFrame += CHAPTER_CARD_FRAMES;

    // Scene slide
    sequences.push(
      <Sequence
        key={`scene_${ch.id}`}
        from={currentFrame}
        durationInFrames={chapterFrames}
      >
        <SceneSlide
          imageFile={`ch_${String(ch.id).padStart(2, "0")}.png`}
          audioFile={`segment_${String(ch.id + 1).padStart(2, "0")}_ch_${String(ch.id).padStart(2, "0")}.mp3`}
          duration={ch.duration_seconds}
          chapterTitle={ch.title}
          chapterIndex={ch.id}
        />
      </Sequence>
    );
    currentFrame += chapterFrames;
  }

  // ── Outro
  sequences.push(
    <Sequence key="outro" from={currentFrame} durationInFrames={OUTRO_FRAMES}>
      <OutroSequence
        primaryColor={brand.color_primary}
        channelName={brand.channel_name}
      />
      <Audio src={staticFile("audio/segment_99_outro.mp3")} />
    </Sequence>
  );

  return <AbsoluteFill>{sequences}</AbsoluteFill>;
};

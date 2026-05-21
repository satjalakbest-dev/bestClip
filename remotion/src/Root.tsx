import { Composition, getInputProps } from "remotion";
import { BlueOclockVideo } from "./compositions/BlueOclockVideo";

// Load script from inputProps (passed via --props flag)
// or use default for preview
const DEFAULT_SCRIPT = {
  title: "Preview Mode",
  brand: { color_primary: "#1B5299", channel_name: "Blue O'Clock" },
  intro: { duration_seconds: 3 },
  chapters: [
    {
      id: 1,
      title: "Chapter 1",
      duration_seconds: 10,
      narration: "ตัวอย่างเนื้อหา",
    },
  ],
  outro: { duration_seconds: 5 },
};

export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps();
  const script = (inputProps as any).script || DEFAULT_SCRIPT;

  // Calculate total duration
  const INTRO_FRAMES = 90; // 3 seconds at 30fps
  const CHAPTER_CARD_FRAMES = 60; // 2 seconds per chapter card
  const OUTRO_FRAMES = 150; // 5 seconds

  const totalFrames =
    INTRO_FRAMES +
    script.chapters.reduce(
      (sum: number, ch: any) =>
        sum + CHAPTER_CARD_FRAMES + Math.ceil(ch.duration_seconds * 30),
      0
    ) +
    OUTRO_FRAMES;

  return (
    <Composition
      id="BlueOclockVideo"
      component={BlueOclockVideo}
      durationInFrames={totalFrames}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ script }}
    />
  );
};

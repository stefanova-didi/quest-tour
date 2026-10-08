import { useId } from "react";
import { AppVersion } from "../components/AppVersion";
import { WelcomeSkyline } from "../components/art";
import { Icon } from "../components/Icon";
import { Paragraphs } from "../components/Paragraphs";
import { formatDateFull, formatHms, formatTime, ordinal } from "../lib/format";
import type { Album, AlbumChapter } from "./types";

/** The team album (design draft): a keepsake page the host shares after the game. A patina cover with the
 *  facts of the day, the host's message, then one chapter per landmark – photo(s), the riddle, the story –
 *  and a closing band. It scrolls as one long page, reads well on a phone and a desktop, and prints one
 *  chapter per page. Unlike the game screens, its text may be selected and copied. */
export function AlbumScreen({ album }: { album: Album }) {
  const tz = album.time_zone;
  return (
    <article className="qa" aria-label={`${album.team} – ${album.game}`}>
      <header className="qa-cover">
        <WelcomeSkyline />
        <p className="qs-hero__kicker">Team album</p>
        <h1 className="t-display-l">{album.game}</h1>
        <span className="qs-team"><Icon name="team" />{album.team}</span>
        <ul className="qa-facts" aria-label="The day in numbers">
          <li><Icon name="calendar" />{formatDateFull(album.played_on, tz)}</li>
          <li><Icon name="flag" />{album.chapters.length} of {album.task_count} landmarks</li>
          {album.total_seconds !== null && <li><Icon name="clock" />{formatHms(album.total_seconds)}</li>}
          {album.rank !== null && (
            <li><Icon name="trophy" />{album.shared_rank ? "Shared " : ""}{ordinal(album.rank)} place</li>
          )}
        </ul>
        <SavePdf />
      </header>
      <main className="qa-main">
        <section className="qs-card qs-host-card" aria-label="From your host">
          <p className="qs-eyebrow qs-eyebrow--gold"><Icon name="gift" />From your host</p>
          <Paragraphs text={album.host_message} />
        </section>
        {album.chapters.map((chapter) => (
          <Chapter key={chapter.number} chapter={chapter} album={album} />
        ))}
        <footer className="qa-end">
          <p className="qs-hero__kicker">The end</p>
          <p className="t-body">{album.team} · {formatDateFull(album.played_on, tz)}</p>
          <SavePdf />
          <AppVersion />
        </footer>
      </main>
    </article>
  );
}

/** "Save as PDF": the browser's print dialog with the album's print stylesheet (A4, the cover on its own
 *  page, then one chapter per page). Every phone and desktop browser offers "Save as PDF" there, so the
 *  team gets a file without the server rendering one; a server-made PDF can replace this later. */
function SavePdf() {
  return (
    <div className="qa-save">
      <button type="button" className="qc-btn qc-btn--gold" onClick={() => window.print()}>
        <Icon name="download" />Save as PDF
      </button>
      <p className="qa-save__hint">Opens the print dialog – choose "Save as PDF".</p>
    </div>
  );
}

function Chapter({ chapter, album }: { chapter: AlbumChapter; album: Album }) {
  const titleId = useId();
  const [first, ...rest] = chapter.photos;
  return (
    <section className="qa-chapter" aria-labelledby={titleId}>
      <p className="qs-eyebrow">
        <Icon name="flag" />Landmark {chapter.number} of {album.task_count} · {formatTime(chapter.reached_at, album.time_zone)}
      </p>
      <h2 id={titleId} className="t-display-l qa-chapter__title">{chapter.landmark}</h2>
      {first && <Photo photo={first} chapter={chapter} album={album} />}
      {rest.length > 0 && (
        <div className="qa-photo-grid">
          {rest.map((photo) => <Photo key={photo.url} photo={photo} chapter={chapter} album={album} small />)}
        </div>
      )}
      <blockquote className="qa-riddle">
        <p className="qs-eyebrow"><Icon name="riddle" />The riddle you solved</p>
        <Paragraphs text={chapter.riddle} />
      </blockquote>
      <section className="qs-card qa-story" aria-label={`The story of ${chapter.landmark}`}>
        <p className="qs-eyebrow qs-eyebrow--gold"><Icon name="bulb" />The story</p>
        <Paragraphs text={chapter.story} />
      </section>
    </section>
  );
}

function Photo({ photo, chapter, album, small = false }: {
  photo: AlbumChapter["photos"][number]; chapter: AlbumChapter; album: Album; small?: boolean;
}) {
  const when = formatTime(photo.taken_at, album.time_zone);
  return (
    <figure className={small ? "qa-photo qa-photo--small" : "qa-photo"}>
      <img src={photo.url} alt={`${album.team} at ${chapter.landmark}, ${when}`} loading="lazy" />
      <figcaption><Icon name="camera" />Team photo · {when}</figcaption>
    </figure>
  );
}

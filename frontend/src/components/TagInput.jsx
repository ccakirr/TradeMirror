import { useId, useMemo, useRef, useState } from "react";

/**
 * A list of short values built one chip at a time.
 *
 * Suggestions narrow as you type; with `free` the typed text can be committed
 * as-is, which is what an account's own setup names need. An empty list is a
 * meaningful answer — "no restriction" — so the field says so rather than
 * looking unfinished.
 */
export default function TagInput({
  label,
  optional,
  placeholder,
  hint,
  emptyLabel,
  addLabel,
  removeLabel,
  suggestions = [],
  value = [],
  onChange,
  free = false,
  limit = 6,
}) {
  const id = useId();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const inputRef = useRef(null);

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return suggestions
      .filter((option) => !value.includes(option.value))
      .filter(
        (option) =>
          !needle ||
          option.value.toLowerCase().includes(needle) ||
          (option.label || "").toLowerCase().includes(needle),
      )
      .slice(0, limit);
  }, [suggestions, value, query, limit]);

  const add = (entry) => {
    const next = entry.trim();
    if (!next || value.includes(next)) {
      setQuery("");
      return;
    }
    onChange([...value, next]);
    setQuery("");
    inputRef.current?.focus();
  };

  const remove = (entry) => {
    onChange(value.filter((item) => item !== entry));
    inputRef.current?.focus();
  };

  // Free text is offered as the first entry rather than a separate control, so
  // committing a name and picking a suggestion are the same gesture.
  const typed = query.trim();
  const offerTyped = free && typed && !value.includes(typed) && !matches.some((m) => m.value === typed);
  const entries = offerTyped ? [{ value: typed, label: addLabel, isNew: true }, ...matches] : matches;

  const onKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      // Enter commits what is being typed; an empty box has nothing to commit,
      // and must never silently add whatever happens to top the list.
      if (typed && entries.length) add(entries[0].value);
      return;
    }
    // Backspace on an empty box walks back through what was already added.
    if (event.key === "Backspace" && !query && value.length) {
      event.preventDefault();
      remove(value[value.length - 1]);
      return;
    }
    if (event.key === "Escape" && open) {
      event.preventDefault();
      event.stopPropagation();
      setOpen(false);
    }
  };

  return (
    <div
      className="field tag-input"
      ref={rootRef}
      onBlur={(event) => {
        if (rootRef.current?.contains(event.relatedTarget)) return;
        setOpen(false);
      }}
    >
      <label htmlFor={id}>
        {label}
        {optional && <em>{optional}</em>}
      </label>

      <div className="tag-control">
        <div className="tag-box">
          {value.map((entry) => (
            <span className="tag" key={entry}>
              {entry}
              <button type="button" onClick={() => remove(entry)} aria-label={`${removeLabel} ${entry}`}>
                ×
              </button>
            </span>
          ))}
          <input
            id={id}
            ref={inputRef}
            type="text"
            autoComplete="off"
            spellCheck="false"
            placeholder={value.length ? "" : placeholder}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
          />
        </div>

        {open && entries.length > 0 && (
          <ul className="tag-suggestions">
            {entries.map((option) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={option.isNew ? "is-new" : ""}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    add(option.value);
                  }}
                >
                  <b>{option.value}</b>
                  {option.label && <span>{option.label}</span>}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <span className="field-hint">{value.length ? hint : emptyLabel}</span>
    </div>
  );
}

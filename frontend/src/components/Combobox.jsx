import { useEffect, useId, useMemo, useRef, useState } from "react";

/**
 * Search-and-pick field: the text box filters, but only a listed option can be
 * committed. Anything typed and left uncommitted reverts on close, so the value
 * handed to the form is always one of `options`.
 */
export default function Combobox({
  label,
  optional,
  placeholder,
  emptyText,
  toggleLabel,
  options,
  value,
  onChange,
  error,
  hint,
  inputRef,
  moreText,
  limit = 60,
}) {
  const id = useId();
  const listId = `${id}-list`;
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;

  const [query, setQuery] = useState(value || "");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef(null);
  const listRef = useRef(null);
  const fallbackRef = useRef(null);
  const control = inputRef || fallbackRef;

  // The committed symbol is what the box shows; typing never changes it.
  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    // Reopening on a committed pick should still offer the whole catalog.
    if (!needle || needle === (value || "").toLowerCase()) return options;
    return options.filter(
      (option) =>
        option.value.toLowerCase().includes(needle) || option.label.toLowerCase().includes(needle),
    );
  }, [options, query, value]);

  // A catalog this size must not put 1400 nodes in the DOM; search narrows it.
  const visible = useMemo(() => filtered.slice(0, limit), [filtered, limit]);
  const hidden = filtered.length - visible.length;

  useEffect(() => {
    setActive(0);
  }, [query]);

  useEffect(() => {
    if (!open) return;
    listRef.current?.children?.[active]?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  const revert = () => {
    setOpen(false);
    setQuery(value || "");
  };

  const pick = (option) => {
    onChange(option.value);
    setQuery(option.value);
    setOpen(false);
    control.current?.focus();
  };

  const onKeyDown = (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setActive((current) => {
        const next = event.key === "ArrowDown" ? current + 1 : current - 1;
        if (next < 0) return visible.length - 1;
        if (next >= visible.length) return 0;
        return next;
      });
      return;
    }

    if (event.key === "Enter" && open && visible[active]) {
      event.preventDefault();
      pick(visible[active]);
      return;
    }

    if (event.key === "Escape" && open) {
      event.preventDefault();
      // Keep the open panel's own Escape handler out of it.
      event.stopPropagation();
      revert();
      return;
    }

    if (event.key === "Home" && open) {
      event.preventDefault();
      setActive(0);
      return;
    }

    if (event.key === "End" && open) {
      event.preventDefault();
      setActive(visible.length - 1);
      return;
    }

    if (event.key === "Tab") revert();
  };

  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ");

  return (
    <div
      className={`field combobox ${error ? "has-error" : ""}`}
      ref={rootRef}
      onBlur={(event) => {
        if (rootRef.current?.contains(event.relatedTarget)) return;
        revert();
      }}
    >
      <label htmlFor={id}>
        {label}
        {optional && <em>{optional}</em>}
      </label>

      <div className="combobox-control">
        <input
          id={id}
          ref={control}
          type="text"
          role="combobox"
          autoComplete="off"
          spellCheck="false"
          placeholder={placeholder}
          value={query}
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && visible[active] ? `${id}-option-${active}` : undefined}
          aria-describedby={describedBy || undefined}
          aria-invalid={error ? "true" : undefined}
          onClick={() => setOpen(true)}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onKeyDown={onKeyDown}
        />

        <button
          type="button"
          className="combobox-toggle"
          tabIndex={-1}
          aria-label={toggleLabel}
          onMouseDown={(event) => {
            // Never let the toggle steal focus from the input.
            event.preventDefault();
            if (open) revert();
            else {
              setOpen(true);
              control.current?.focus();
            }
          }}
        >
          ▾
        </button>

        {open && (
          <ul className="combobox-list" id={listId} role="listbox" ref={listRef}>
            {visible.length ? (
              visible.map((option, index) => (
                <li
                  key={option.value}
                  id={`${id}-option-${index}`}
                  role="option"
                  aria-selected={option.value === value}
                  className={index === active ? "active" : ""}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    pick(option);
                  }}
                  onMouseEnter={() => setActive(index)}
                >
                  <b>{option.value}</b>
                  <span>{option.label}</span>
                  {option.tag && <small>{option.tag}</small>}
                </li>
              ))
            ) : (
              <li className="combobox-empty">{emptyText}</li>
            )}
            {hidden > 0 && <li className="combobox-more">{moreText?.(hidden)}</li>}
          </ul>
        )}
      </div>

      {hint && !error && (
        <span className="field-hint" id={hintId}>
          {hint}
        </span>
      )}
      {error && (
        <span className="field-error" id={errorId}>
          {error}
        </span>
      )}
    </div>
  );
}

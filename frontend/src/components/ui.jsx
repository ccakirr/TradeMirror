import { cloneElement, createContext, useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from "react";

export function Spinner({ label }) {
  return <span className="spinner" role="status" aria-label={label} />;
}

export function Button({
  variant = "primary",
  pending,
  chevron,
  children,
  className = "",
  type = "button",
  disabled,
  ...rest
}) {
  return (
    <button
      {...rest}
      type={type}
      className={`button ${variant} ${pending ? "is-pending" : ""} ${className}`.trim()}
      // A pending request must not be fired twice by an impatient second click.
      disabled={disabled || pending}
      aria-busy={pending || undefined}
    >
      {pending && <Spinner />}
      <span>{children}</span>
      {chevron && !pending && <b aria-hidden="true">{chevron}</b>}
    </button>
  );
}

/** Wires label, hint and error message to the control so screen readers announce them. */
export function Field({ label, hint, error, optional, affix, children }) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ");

  return (
    <div className={`field ${error ? "has-error" : ""}`}>
      <label htmlFor={id}>
        {label}
        {optional && <em>{optional}</em>}
      </label>
      {affix ? (
        <div className="input-affix">
          {cloneElement(children, {
            id,
            "aria-describedby": describedBy || undefined,
            "aria-invalid": error ? "true" : undefined,
          })}
          {affix}
        </div>
      ) : (
        cloneElement(children, {
          id,
          "aria-describedby": describedBy || undefined,
          "aria-invalid": error ? "true" : undefined,
        })
      )}
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

/** A rule that is either in force or it isn't — a switch reads that faster than a checkbox. */
export function Toggle({ label, hint, checked, onChange }) {
  return (
    <label className={`toggle ${checked ? "on" : ""}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="toggle-track" aria-hidden="true">
        <i />
      </span>
      <span className="toggle-copy">
        <b>{label}</b>
        {hint && <small>{hint}</small>}
      </span>
    </label>
  );
}

export function Badge({ tone = "neutral", children }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function Skeleton({ width, height = 14, radius = 4 }) {
  return <span className="skeleton" style={{ width, height, borderRadius: radius }} aria-hidden="true" />;
}

export function EmptyState({ icon = "＋", title, text, action, compact }) {
  return (
    <div className={`empty-state ${compact ? "compact" : ""}`}>
      <div className="empty-icon" aria-hidden="true">
        {icon}
      </div>
      <h3>{title}</h3>
      {text && <p>{text}</p>}
      {action}
    </div>
  );
}

/** Radio-group segmented control. */
export function Segmented({ label, value, options, onChange }) {
  return (
    <div className="segmented" role="radiogroup" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={option.value === value}
          className={option.value === value ? "selected" : ""}
          onClick={() => onChange(option.value)}
        >
          {option.label}
          {option.count !== undefined && <small>{option.count}</small>}
        </button>
      ))}
    </div>
  );
}

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (message, tone = "success") => {
      const id = ++toastId;
      setToasts((current) => [...current, { id, message, tone }]);
      timers.current.set(
        id,
        setTimeout(() => dismiss(id), tone === "error" ? 6000 : 4000),
      );
      return id;
    },
    [dismiss],
  );

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);

  const value = useMemo(() => Object.assign(push, { dismiss }), [push, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toaster" role="status" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.tone}`}>
            <span aria-hidden="true">{toast.tone === "error" ? "!" : "✓"}</span>
            <p>{toast.message}</p>
            <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss">
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

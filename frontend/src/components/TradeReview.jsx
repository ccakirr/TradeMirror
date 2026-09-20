import { useEffect, useState } from "react";
import { Button, Field } from "./ui";

const EMPTY = {
  plan_adherence: "followed",
  setup_followed: true,
  pre_trade_emotion: "",
  post_trade_emotion: "",
  mistake_tags: "",
  lesson: "",
};

export default function TradeReview({ t, review, onSave }) {
  const [form, setForm] = useState(EMPTY);
  const [open, setOpen] = useState(!review);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (review) {
      setForm({
        ...review,
        mistake_tags: (review.mistake_tags || []).join(", "),
      });
      setOpen(false);
    }
  }, [review]);

  const update = (key) => (event) => {
    const value = key === "setup_followed" ? event.target.value === "true" : event.target.value;
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await onSave({
        ...form,
        mistake_tags: form.mistake_tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      setOpen(false);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="trade-review-block">
      <div className="review-head">
        <div>
          <p className="eyebrow">{t("reviewTag")}</p>
          <h3>{t("reviewTitle")}</h3>
        </div>
        {review && <Button variant="ghost" className="compact" onClick={() => setOpen((value) => !value)}>{open ? t("cancel") : t("edit")}</Button>}
      </div>

      {open ? (
        <form className="trade-review-form" onSubmit={submit}>
          <div className="review-fields">
            <Field label={t("planAdherence")}>
              <select value={form.plan_adherence} onChange={update("plan_adherence")}>
                <option value="followed">{t("reviewFollowed")}</option>
                <option value="partially_followed">{t("reviewPartial")}</option>
                <option value="broken">{t("reviewBroken")}</option>
                <option value="unknown">{t("reviewUnknown")}</option>
              </select>
            </Field>
            <Field label={t("setupFollowed")}>
              <select value={String(form.setup_followed)} onChange={update("setup_followed")}>
                <option value="true">{t("yes")}</option>
                <option value="false">{t("no")}</option>
              </select>
            </Field>
            <Field label={t("preEmotion")} optional={t("optional")}>
              <input value={form.pre_trade_emotion} onChange={update("pre_trade_emotion")} placeholder={t("emotionPlaceholder")} />
            </Field>
            <Field label={t("postEmotion")} optional={t("optional")}>
              <input value={form.post_trade_emotion} onChange={update("post_trade_emotion")} placeholder={t("emotionPlaceholder")} />
            </Field>
          </div>
          <Field label={t("mistakeTags")} optional={t("optional")} hint={t("mistakeTagsHint")}>
            <input value={form.mistake_tags} onChange={update("mistake_tags")} placeholder={t("mistakeTagsPlaceholder")} />
          </Field>
          <Field label={t("lesson")} optional={t("optional")}>
            <textarea rows="3" value={form.lesson} onChange={update("lesson")} placeholder={t("lessonPlaceholder")} />
          </Field>
          <Button type="submit" variant="primary" pending={pending}>{pending ? t("saving") : t("saveReview")}</Button>
          {error && <p className="form-message" role="alert">{error}</p>}
        </form>
      ) : (
        <div className="review-summary">
          <span>{t("planAdherence")}: <b>{t(`review_${review.plan_adherence}`)}</b></span>
          <span>{t("setupFollowed")}: <b>{review.setup_followed ? t("yes") : t("no")}</b></span>
          {review.lesson && <p>{review.lesson}</p>}
        </div>
      )}
    </section>
  );
}

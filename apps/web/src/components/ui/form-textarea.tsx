type FormTextareaProps = {
  error?: string;
  helper?: string;
  id: string;
  label: string;
  placeholder: string;
  rows?: number;
  value: string;
  onChange: (value: string) => void;
};

export function FormTextarea({
  error,
  helper,
  id,
  label,
  onChange,
  placeholder,
  rows = 4,
  value
}: FormTextareaProps) {
  return (
    <label className="form-field" htmlFor={id}>
      <span className="form-label">{label}</span>
      <textarea
        aria-invalid={Boolean(error)}
        className="form-input form-textarea"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={rows}
        value={value}
      />
      {helper ? <span className="form-helper">{helper}</span> : null}
      {error ? <span className="form-error">{error}</span> : null}
    </label>
  );
}

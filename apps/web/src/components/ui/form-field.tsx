type FormFieldProps = {
  error?: string;
  helper?: string;
  id: string;
  label: string;
  placeholder: string;
  required?: boolean;
  type?: "email" | "password" | "text";
  value: string;
  onChange: (value: string) => void;
};

export function FormField({
  error,
  helper,
  id,
  label,
  onChange,
  placeholder,
  required = false,
  type = "text",
  value
}: FormFieldProps) {
  return (
    <label className="form-field" htmlFor={id}>
      <span className="form-label">{label}</span>
      <input
        aria-invalid={Boolean(error)}
        className="form-input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        type={type}
        value={value}
      />
      {helper ? <span className="form-helper">{helper}</span> : null}
      {error ? <span className="form-error">{error}</span> : null}
    </label>
  );
}

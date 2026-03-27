// Form validation utilities. Each returns an error message string or null if valid.

export function required(value: string | null | undefined): string | null {
  if (!value || value.trim().length === 0) {
    return 'Este campo es obligatorio';
  }
  return null;
}

export function minLength(min: number) {
  return (value: string | null | undefined): string | null => {
    if (!value || value.trim().length < min) {
      return `Debe tener al menos ${min} caracteres`;
    }
    return null;
  };
}

export function maxLength(max: number) {
  return (value: string | null | undefined): string | null => {
    if (value && value.length > max) {
      return `No puede superar los ${max} caracteres`;
    }
    return null;
  };
}

export function isEmail(value: string | null | undefined): string | null {
  if (!value) return null; // use `required` separately if needed
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return 'Email no valido';
  }
  return null;
}

/**
 * Compose multiple validators. Returns the first error found, or null.
 */
export function compose(
  ...validators: Array<(value: string | null | undefined) => string | null>
) {
  return (value: string | null | undefined): string | null => {
    for (const validate of validators) {
      const error = validate(value);
      if (error) return error;
    }
    return null;
  };
}

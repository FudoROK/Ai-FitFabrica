export type DemoRequestDto = {
  name: string;
  email: string;
  company?: string;
  message?: string;
};

export type SignInDto = {
  email: string;
  password: string;
};

import { RouterProvider } from 'react-router-dom';
import { router } from '@/router/index';

interface Props {}

export function App(_props: Props) {
  return <RouterProvider router={router} />;
}

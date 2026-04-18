import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Home from './DashboardLayout';

const useClassesWithAssignmentsMock = vi.fn();
const isTeacherMock = vi.fn();
const isAdminMock = vi.fn();

vi.mock('../classes/useClasses', () => ({
  useClassesWithAssignments: (...args: unknown[]) => useClassesWithAssignmentsMock(...args),
}));

vi.mock('../../util/login', () => ({
  isTeacher: () => isTeacherMock(),
  isAdmin: () => isAdminMock(),
}));

function renderWithQueryClient(ui: Parameters<typeof render>[0]) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Home US19 course access', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isTeacherMock.mockReturnValue(false);
    isAdminMock.mockReturnValue(false);
    useClassesWithAssignmentsMock.mockReturnValue({
      data: [],
      isLoading: false,
    });
  });

  it('shows a helpful empty state for students with no courses', async () => {
    useClassesWithAssignmentsMock.mockReturnValue({
      data: [],
      isLoading: false,
    });

    renderWithQueryClient(<Home />);

    expect(await screen.findByText('Peer Review Dashboard')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'CS 101' })).not.toBeInTheDocument();
  });

  it('renders registered courses on dashboard', async () => {
    useClassesWithAssignmentsMock.mockReturnValue({
      data: [{ id: 42, name: 'CS 101', assignmentCount: 0, image_path: null }],
      isLoading: false,
    });

    renderWithQueryClient(<Home />);

    expect(await screen.findByText('CS 101')).toBeInTheDocument();
    expect(screen.getByText('0 assignments')).toBeInTheDocument();
  });
});

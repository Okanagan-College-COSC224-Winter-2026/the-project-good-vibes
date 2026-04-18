import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ClassHome from './ClassHome';

const createAssignmentMock = vi.fn();
const useAssignmentsMock = vi.fn();
const useCreateAssignmentMock = vi.fn();
const isTeacherMock = vi.fn();

vi.mock('../assignments/useAssignments', () => ({
  useAssignments: (...args: unknown[]) => useAssignmentsMock(...args),
  useCreateAssignment: (...args: unknown[]) => useCreateAssignmentMock(...args),
}));

vi.mock('../../util/login', () => ({
  isTeacher: () => isTeacherMock(),
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
      {ui}
    </QueryClientProvider>
  );
}

describe('ClassHome US9 create-assignment flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isTeacherMock.mockReturnValue(true);
    useAssignmentsMock.mockReturnValue({ data: [] });
    useCreateAssignmentMock.mockReturnValue({
      mutate: createAssignmentMock,
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null,
    });
  });

  it('defaults anonymity checkbox to checked and submits true', async () => {
    renderWithQueryClient(
      <MemoryRouter initialEntries={['/classes/42/home']}>
        <Routes>
          <Route path='/classes/:id/home' element={<ClassHome />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('Assignments');

    fireEvent.click(screen.getByText('+ New Assignment'));

    const checkbox = screen.getByRole('checkbox', { name: /anonymous submissions\/reviews/i });
    expect(checkbox).toBeChecked();

    const nameInput = screen.getByPlaceholderText('Enter assignment name...');
    fireEvent.input(nameInput, { target: { value: 'US9 Anonymous Assignment' } });

    fireEvent.click(screen.getByText('Create Assignment'));

    await waitFor(() => {
      expect(createAssignmentMock).toHaveBeenCalledWith(
        {
          courseID: 42,
          name: 'US9 Anonymous Assignment',
          description: undefined,
          start_date: undefined,
          due_date: undefined,
          is_anonymous: true,
        },
        expect.objectContaining({
          onSuccess: expect.any(Function),
        }),
      );
    });
  });
});

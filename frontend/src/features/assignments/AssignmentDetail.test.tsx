import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Assignment from './AssignmentDetail';

const useAssignmentDetailMock = vi.fn();

function makeAssignmentDetailState() {
  return {
    classId: '10',
    assignmentId: 5,
    assignment: {
      id: 5,
      courseID: 10,
      name: 'Assignment Title',
      description: 'Assignment description',
      is_anonymous: true,
    },
    teacherMode: true,
    isManageTab: false,
    rubricId: null,
    groupRubricId: null,
    review: [],
    groupReview: [],
    resourceList: [],
    groupMembers: [],
    otherGroups: [],
    mySubmission: null,
    revieweeID: 0,
    setRevieweeID: vi.fn(),
    groupRevieweeID: 0,
    setGroupRevieweeID: vi.fn(),
  };
}

vi.mock('../reviews/RubricCreator', () => ({
  default: () => <div>Rubric Creator</div>,
}));

vi.mock('../reviews/RubricDisplay', () => ({
  default: () => <div>Rubric Display</div>,
}));

vi.mock('./useAssignmentDetail', () => ({
  useAssignmentDetail: () => useAssignmentDetailMock(),
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

describe('Assignment US9 UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAssignmentDetailMock.mockReturnValue(makeAssignmentDetailState());
  });

  it('renders tabs above assignment header on manage route', async () => {
    useAssignmentDetailMock.mockReturnValue({
      ...makeAssignmentDetailState(),
      teacherMode: true,
      isManageTab: true,
    });
    window.history.pushState({}, '', '/classes/10/assignments/5/manage');

    const { container } = renderWithQueryClient(
      <MemoryRouter initialEntries={['/classes/10/assignments/5/manage']}>
        <Routes>
          <Route path='/classes/:id/assignments/:assignmentId/manage' element={<Assignment />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('Management');
    await screen.findByText('Assignment Title');

    const tabNav = container.querySelector('.TabNav');
    const header = screen.getByText('Assignment Title');

    expect(tabNav).not.toBeNull();
    expect((tabNav?.compareDocumentPosition(header) ?? 0) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('shows teacher student-preview resources section in review tab', async () => {
    useAssignmentDetailMock.mockReturnValue({
      ...makeAssignmentDetailState(),
      teacherMode: true,
      isManageTab: false,
      resourceList: [
        {
          id: 1,
          assignmentID: 5,
          uploaderID: 3,
          original_name: 'guide.pdf',
          download_url: '/assignment-resource/file/1',
        },
      ],
    });

    window.history.pushState({}, '', '/classes/10/assignments/5');

    renderWithQueryClient(
      <MemoryRouter initialEntries={['/classes/10/assignments/5']}>
        <Routes>
          <Route path='/classes/:id/assignments/:assignmentId' element={<Assignment />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Documents (Student Preview)')).toBeInTheDocument();
    expect(screen.getByText('guide.pdf')).toBeInTheDocument();
  });

  it('shows student attachment workflow section in home tab', async () => {
    useAssignmentDetailMock.mockReturnValue({
      ...makeAssignmentDetailState(),
      teacherMode: false,
      isManageTab: false,
      resourceList: [],
      mySubmission: null,
    });

    window.history.pushState({}, '', '/classes/10/assignments/5');

    renderWithQueryClient(
      <MemoryRouter initialEntries={['/classes/10/assignments/5']}>
        <Routes>
          <Route path='/classes/:id/assignments/:assignmentId' element={<Assignment />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('My Attachment')).toBeInTheDocument();
    });

    expect(screen.getByText('Upload Attachment')).toBeInTheDocument();
    expect(screen.getByText('Supporting Documents')).toBeInTheDocument();
  });
});

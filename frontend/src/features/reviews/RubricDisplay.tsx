import Criteria from './Criteria';
import { useRubric, useCriteria } from './useRubric';

interface RubricDisplayProps {
    rubricId: number | null;
    onCriterionSelect: (row: number, column: number) => void;
    onCommentChange?: (comment: string) => void;
    grades: number[];
    comment?: string;
}

export default function RubricDisplay({ rubricId, onCriterionSelect, onCommentChange, grades, comment }: RubricDisplayProps) {
    const { data: criteria = [] } = useCriteria(rubricId);
    const { data: rubricInfo } = useRubric(rubricId);

    const questions: string[] = [];
    const scoreMaxes: number[] = [];
    const hasScores: boolean[] = [];

    criteria.forEach((crit: Criterion) => {
        questions.push(crit.question);
        scoreMaxes.push(crit.scoreMax);
        hasScores.push(crit.hasScore);
    });

    if (!rubricId || criteria.length === 0) {
        return (
            <div className="flex flex-col items-center gap-2 py-4">
                <span className="text-3xl">📋</span>
                <p className="text-text-secondary text-sm m-0">No rubric available yet.</p>
            </div>
        );
    }

    return (
        <Criteria
            questions={questions}
            scoreMaxes={scoreMaxes}
            canComment={rubricInfo?.canComment ?? false}
            hasScores={hasScores}
            onCriterionSelect={(row: number, value: number) => {
                const criterionId = criteria[row]?.id;
                if (criterionId !== undefined) {
                    onCriterionSelect(criterionId, value);
                }
            }}
            onCommentChange={onCommentChange}
            grades={grades}
            comment={comment}
        />
    );
}

import { useState } from 'react';
import toast from 'react-hot-toast';
import Button from '../../ui/Button';
import { useCreateRubric } from './useRubric';

interface RubricCreatorProps {
    onRubricCreated?: (rubricId: number) => void;
    id: number;
    rubricType?: "individual" | "group";
}

export default function RubricCreator({ onRubricCreated, id, rubricType = "individual" }: RubricCreatorProps) {
    const [newCriteria, setNewCriteria] = useState<Omit<Criterion, 'id'>[]>([
        { rubricID: 0, question: '', scoreMax: 1, hasScore: true }
    ]);
    const [canComment, setCanComment] = useState(false);

    const { mutate: createRubric, isPending } = useCreateRubric(id, rubricType);

    const handleCreate = () => {
        const emptyQuestions = newCriteria.some(c => !c.question.trim());
        if (emptyQuestions) {
            toast.error('Please fill in all criterion questions.');
            return;
        }

        createRubric(
            { canComment, criteria: newCriteria.map(({ question, scoreMax, hasScore }) => ({ question, scoreMax, hasScore })) },
            {
                onSuccess: (rubricId) => {
                    toast.success('Rubric created successfully!');
                    if (onRubricCreated) onRubricCreated(rubricId);
                },
                onError: (error) => {
                    console.error("Error creating rubric:", error);
                    toast.error('Failed to create rubric.');
                },
            }
        );
    };

    const handleQuestionChange = (index: number, value: string) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].question = value;
        setNewCriteria(updatedCriteria);
    };

    const handleScoreMaxChange = (index: number, value: number) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].scoreMax = Math.min(100, Math.max(1, value));
        setNewCriteria(updatedCriteria);
    };

    const handleHasScoreChange = (index: number, value: boolean) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].hasScore = value;
        if (!value) {
            updatedCriteria[index].scoreMax = 1;
        }
        setNewCriteria(updatedCriteria);
    };

    const handleAddNewSection = () => setNewCriteria(prev => [...prev, { rubricID: 0, question: '', scoreMax: 1, hasScore: true } as Omit<Criterion, 'id'>]);

    const handleRemoveSection = (index: number) => setNewCriteria(prev => prev.filter((_, i) => i !== index));

    return (
        <div className="flex flex-col gap-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <h2 className="text-lg font-semibold text-text-primary m-0">Create Rubric</h2>
                <label className="flex items-center gap-2.5 text-sm text-text-secondary cursor-pointer select-none">
                    <div className={`relative w-9 h-5 rounded-full transition-colors ${canComment ? 'bg-btn-primary' : 'bg-gray-300'}`}
                         onClick={() => setCanComment(prev => !prev)}>
                        <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${canComment ? 'translate-x-4' : ''}`} />
                    </div>
                    Allow comments
                </label>
            </div>

            <div className="flex flex-col gap-3">
                {newCriteria.map((item, index) => (
                    <div key={index} className="group flex flex-col gap-3 p-4 bg-bg-secondary rounded-xl border border-border hover:border-btn-primary/30 transition-colors">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-text-secondary uppercase tracking-wide">
                                Criterion {index + 1}
                            </span>
                            {newCriteria.length > 1 && (
                                <button
                                    onClick={() => handleRemoveSection(index)}
                                    className="text-xs px-2.5 py-1 rounded-md text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 cursor-pointer transition-colors"
                                >
                                    Remove
                                </button>
                            )}
                        </div>
                        <input
                            type="text"
                            value={item.question}
                            onChange={(e) => handleQuestionChange(index, e.target.value)}
                            placeholder="e.g. How well did the student communicate their ideas?"
                            className="w-full px-3.5 py-2.5 border border-border rounded-lg bg-white text-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
                        />
                        <div className="flex flex-wrap items-center gap-4">
                            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={item.hasScore}
                                    onChange={(e) => handleHasScoreChange(index, e.target.checked)}
                                    className="w-4 h-4 accent-btn-primary"
                                />
                                Scored
                            </label>
                            {item.hasScore && (
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-text-secondary">Max:</span>
                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={item.scoreMax}
                                        onChange={(e) => handleScoreMaxChange(index, Number(e.target.value))}
                                        className="w-16 px-2.5 py-1.5 border border-border rounded-lg bg-white text-sm text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <button
                onClick={handleAddNewSection}
                className="w-full py-3 border-2 border-dashed border-border rounded-xl text-sm font-medium text-text-secondary hover:border-btn-primary/40 hover:text-btn-primary hover:bg-btn-primary/5 transition-all cursor-pointer bg-transparent"
            >
                + Add Criterion
            </button>

            <div className="flex justify-end pt-2">
                <Button onClick={handleCreate} disabled={isPending}>
                    {isPending ? "Creating..." : "Create Rubric"}
                </Button>
            </div>
        </div>
    );
}

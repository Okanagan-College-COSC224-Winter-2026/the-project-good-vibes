import Criterion from './Criterion';
import { useState, useEffect } from 'react';

interface props {
    questions: Array<string>;
    scoreMaxes: Array<number>;
    canComment: boolean;
    hasScores: Array<boolean>;
    onCriterionSelect: (row: number, column: number) => void;
    onCommentChange?: (comment: string) => void;
    grades: number[];
    comment?: string;
}

export default function Criteria(props: props) {
    const [scores, setScores] = useState<number[]>(
        props.grades.length > 0 ? [...props.grades] : new Array(props.questions.length).fill(0)
    );

    useEffect(() => {
        if (props.grades.length > 0) {
            setScores([...props.grades]);
        }
    }, [props.grades]);

    const handleSelect = (row: number, value: number) => {
        setScores(prev => {
            const updated = [...prev];
            updated[row] = value;
            return updated;
        });
        props.onCriterionSelect(row, value);
    };

    const currentTotal = scores.reduce((sum, score, i) => props.hasScores[i] ? sum + score : sum, 0);
    const maxTotal = props.scoreMaxes.reduce((sum, max, i) => props.hasScores[i] ? sum + max : sum, 0);

    return (
        <div className="flex flex-col gap-3 w-full">
            {props.questions.map((question, i) => (
                <Criterion
                    key={i}
                    question={question}
                    scoreMax={props.scoreMaxes[i]}
                    hasScore={props.hasScores[i]}
                    onCriterionSelect={handleSelect}
                    questionIndex={i}
                    grade={props.grades[i]}
                />
            ))}

            {props.canComment && (
                <div className="mt-1">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide block mb-2">Additional Comments</label>
                    <textarea
                        className="w-full min-h-[80px] px-3.5 py-2.5 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm font-[inherit] resize-y focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
                        placeholder="Additional comments..."
                        value={props.comment ?? ""}
                        onChange={(e) => props.onCommentChange?.(e.target.value)}
                    />
                </div>
            )}

            {maxTotal > 0 && (
                <div className="flex justify-between items-center mt-2 pt-3 border-t border-border">
                    <span className="text-sm font-semibold text-text-primary">Total</span>
                    <span className="text-sm font-bold text-btn-primary bg-btn-primary/10 px-3 py-1 rounded-full">
                        {currentTotal} / {maxTotal}
                    </span>
                </div>
            )}
        </div>
    );
}

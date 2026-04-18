import { useState, useEffect } from 'react';

interface props {
    question: string;
    scoreMax: number;
    hasScore: boolean;
    onCriterionSelect: (row: number, column: number) => void;
    questionIndex: number;
    grade: number;
}

export default function Criterion(props: props) {
    const [sliderValue, setSliderValue] = useState<number>(props.grade || 0);

    useEffect(() => {
        setSliderValue(props.grade || 0);
    }, [props.grade]);

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = Number(e.target.value);
        setSliderValue(value);
        props.onCriterionSelect(props.questionIndex, value);
    };

    return (
        <div className="rounded-xl border border-border px-5 py-4 transition-colors hover:border-btn-primary/20">
            <p className="font-medium text-text-primary text-sm mb-3 m-0">{props.question}</p>

            {props.hasScore ? (
                <div className="flex items-center gap-4">
                    <input
                        type="range"
                        min={0}
                        max={props.scoreMax}
                        value={sliderValue}
                        onChange={handleSliderChange}
                        className="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-btn-primary bg-bg-secondary"
                    />
                    <span className="text-sm font-semibold text-btn-primary bg-btn-primary/10 px-2.5 py-0.5 rounded-full whitespace-nowrap min-w-[3.5rem] text-center">
                        {sliderValue} / {props.scoreMax}
                    </span>
                </div>
            ) : (
                <textarea
                    className="w-full min-h-[80px] px-3.5 py-2.5 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm font-[inherit] resize-y focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all"
                    placeholder="Write your comment here..."
                />
            )}
        </div>
    );
}

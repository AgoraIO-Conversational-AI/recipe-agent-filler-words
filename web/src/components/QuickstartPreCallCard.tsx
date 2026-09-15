"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { FillerWordsMode } from "@/types/conversation";

type QuickstartPreCallCardProps = {
	isLoading: boolean;
	error: string | null;
	fillerWordsMode: FillerWordsMode | null;
	onFillerWordsModeChange: (mode: FillerWordsMode) => void;
	onStartConversation: () => void;
};

export function QuickstartPreCallCard({
	isLoading,
	error,
	fillerWordsMode,
	onFillerWordsModeChange,
	onStartConversation,
}: QuickstartPreCallCardProps) {
	const isConfigLoading = fillerWordsMode === null && error === null;
	return (
		<div
			className="mx-auto flex w-[min(92vw,26.25rem)] animate-fade-up flex-col items-center rounded-[20px] border border-[#2b2b2b] px-10 py-10 text-center shadow-[0_10px_24px_rgba(0,0,0,0.28)]"
			style={{
				backgroundImage:
					"linear-gradient(164.988deg, rgba(54,54,54,0.2) 1.0596%, rgba(0,0,0,0) 96.089%), linear-gradient(90deg, rgb(16,16,16) 0%, rgb(16,16,16) 100%)",
			}}
		>
			<h1 className="text-[28px] font-medium leading-[1.2] text-white">
				Filler Words
			</h1>
			<p className="mt-[14px] text-sm font-medium leading-6 text-muted-foreground">
				Hear natural filler phrases while the agent thinks, and a graceful
				goodbye when you hang up.
			</p>

			<fieldset
				disabled={isLoading || fillerWordsMode === null}
				className="mt-8 w-full text-left"
			>
				<legend className="mb-3 text-sm font-medium text-white">
					Filler mode
				</legend>
				<div className="grid grid-cols-2 gap-2">
					{(["static", "generated"] as const).map((mode) => (
						<label key={mode} className="cursor-pointer">
							<input
								type="radio"
								name="fillerWordsMode"
								value={mode}
								checked={fillerWordsMode === mode}
								onChange={() => onFillerWordsModeChange(mode)}
								aria-describedby="filler-mode-description"
								className="peer sr-only"
							/>
							<span className="flex h-10 items-center justify-center rounded-lg border border-[#2b2b2b] text-sm text-muted-foreground transition-colors peer-checked:border-primary peer-checked:bg-primary/10 peer-checked:text-primary peer-focus-visible:ring-2 peer-focus-visible:ring-primary peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-background peer-disabled:cursor-not-allowed peer-disabled:opacity-50">
								{mode === "static" ? "Static" : "Generated"}
							</span>
						</label>
					))}
				</div>
				<p
					id="filler-mode-description"
					className="mt-3 min-h-10 text-xs leading-5 text-muted-foreground"
				>
					{fillerWordsMode === null
						? isConfigLoading
							? "Loading filler mode..."
							: "Filler mode is unavailable."
						: fillerWordsMode === "static"
							? "Plays a phrase from a built-in list while the agent thinks."
							: "Generates a phrase based on what you said, with built-in phrases as a fallback."}
				</p>
			</fieldset>

			<Button
				onClick={onStartConversation}
				disabled={isLoading || fillerWordsMode === null}
				className="mt-6 h-10 w-full rounded-lg border border-primary bg-primary text-sm font-medium text-black hover:border-white hover:bg-white hover:text-black disabled:hover:border-primary disabled:hover:bg-primary disabled:hover:text-black"
				aria-label={
					isConfigLoading
						? "Loading conversation settings"
						: isLoading
							? "Starting conversation with AI agent"
							: "Start conversation with AI agent"
				}
			>
				{isLoading || isConfigLoading ? (
					<>
						<Loader2 className="h-4 w-4 animate-spin" />
						{isConfigLoading ? "Loading settings..." : "Starting..."}
					</>
				) : (
					"Start Conversation"
				)}
			</Button>
			{error ? <p className="mt-3 text-xs text-destructive">{error}</p> : null}
		</div>
	);
}

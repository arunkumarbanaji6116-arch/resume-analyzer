"use client";

import { useState, useMemo } from "react";
import { Drawer } from "vaul";
import useMeasure from "react-use-measure";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { X, FileText, Video, SearchCheck, ArrowRight } from "lucide-react";

interface WorkspaceTool {
  id: "resume" | "interview" | "jobs";
  title: string;
  subtitle: string;
  description: string;
  action: string;
  href: string;
  icon: React.ElementType;
  badgeColor: string;
}

const WORKSPACE_TOOLS: Record<string, WorkspaceTool> = {
  resume: {
    id: "resume",
    title: "Resume Review",
    subtitle: "Improve your story",
    description: "Get practical, role-focused feedback that makes your experience clear and memorable.",
    action: "Review my resume",
    href: "/resume",
    icon: FileText,
    badgeColor: "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-400"
  },
  interview: {
    id: "interview",
    title: "Interview Lab",
    subtitle: "Practice with structure",
    description: "Practice tailored questions, refine your answers, and walk into interviews with more confidence.",
    action: "Start practice",
    href: "/interview",
    icon: Video,
    badgeColor: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
  },
  jobs: {
    id: "jobs",
    title: "Job Analyzer",
    subtitle: "Check your fit",
    description: "Compare a job opportunity with your strengths and see where to focus before applying.",
    action: "Analyze a job",
    href: "/jobs",
    icon: SearchCheck,
    badgeColor: "bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-400"
  }
};

export function CareerWorkspaceGrid() {
  const [selectedTool, setSelectedTool] = useState<WorkspaceTool | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [elementRef, bounds] = useMeasure();

  const handleOpenTool = (toolKey: string) => {
    setSelectedTool(WORKSPACE_TOOLS[toolKey]);
    setIsOpen(true);
  };

  return (
    <div className="w-full max-w-5xl mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-50">
          Your career workspace
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400 mt-1">
          Choose a focus area to step into your next career move.
        </p>
      </div>

      {/* 3 Workspace Boxes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.values(WORKSPACE_TOOLS).map((tool) => {
          const IconComponent = tool.icon;
          return (
            <button
              key={tool.id}
              onClick={() => handleOpenTool(tool.id)}
              className="group relative flex flex-col justify-between p-6 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl text-left shadow-sm hover:shadow-md hover:-translate-y-1 hover:border-indigo-500 transition-all duration-200"
            >
              <div>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 ${tool.badgeColor}`}>
                  <IconComponent className="w-5 h-5" />
                </div>
                <strong className="block text-lg font-bold text-neutral-900 dark:text-neutral-100">
                  {tool.title}
                </strong>
                <span className="block text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                  {tool.subtitle}
                </span>
              </div>
              <em className="inline-flex items-center gap-1 not-italic text-xs font-semibold text-indigo-600 dark:text-indigo-400 mt-4 group-hover:underline">
                Open space <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
              </em>
            </button>
          );
        })}
      </div>

      {/* Animated Bottom Drawer */}
      <Drawer.Root open={isOpen} onOpenChange={setIsOpen}>
        <Drawer.Portal>
          <Drawer.Overlay
            className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40"
            onClick={() => setIsOpen(false)}
          />
          <Drawer.Content
            asChild
            className="fixed inset-x-4 bottom-4 z-50 mx-auto max-w-[440px] overflow-hidden rounded-[32px] bg-white dark:bg-neutral-900 shadow-2xl border border-neutral-200 dark:border-neutral-800 outline-none"
          >
            <motion.div animate={{ height: bounds.height || "auto" }}>
              <div className="p-6" ref={elementRef}>
                {selectedTool && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${selectedTool.badgeColor}`}>
                        <selectedTool.icon className="w-6 h-6" />
                      </div>
                      <Button
                        variant="secondary"
                        size="icon"
                        className="rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800"
                        onClick={() => setIsOpen(false)}
                      >
                        <X className="text-neutral-600 dark:text-neutral-400" size={18} />
                      </Button>
                    </div>

                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                        YOUR NEXT STEP
                      </span>
                      <h2 className="text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 mt-1">
                        {selectedTool.title}
                      </h2>
                      <p className="text-neutral-500 dark:text-neutral-400 text-sm mt-1">
                        {selectedTool.subtitle}
                      </p>
                    </div>

                    <p className="text-neutral-600 dark:text-neutral-300 text-sm leading-relaxed">
                      {selectedTool.description}
                    </p>

                    <div className="pt-2 flex flex-col gap-2">
                      <a
                        href={selectedTool.href}
                        className="w-full inline-flex items-center justify-center py-3.5 px-6 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-md transition-all"
                      >
                        {selectedTool.action}
                      </a>
                      <Button
                        variant="ghost"
                        onClick={() => setIsOpen(false)}
                        className="w-full text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 rounded-xl"
                      >
                        Maybe later
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </Drawer.Content>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

export default CareerWorkspaceGrid;

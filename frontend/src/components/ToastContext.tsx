import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import type { AlertSeverity } from "../services/api";

export interface Toast {
  id: string;
  message: string;
  severity: AlertSeverity;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (message: string, severity?: AlertSeverity) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  addToast: () => undefined,
  removeToast: () => undefined,
});

let _counter = 0;

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: string) => {
    clearTimeout(timers.current.get(id));
    timers.current.delete(id);
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, severity: AlertSeverity = "medium") => {
      const id = `toast-${++_counter}`;
      setToasts((prev) => [...prev.slice(-4), { id, message, severity }]);
      const timeout = severity === "critical" ? 8000 : 5000;
      timers.current.set(id, setTimeout(() => removeToast(id), timeout));
    },
    [removeToast],
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);

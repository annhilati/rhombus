import { useState, useEffect } from 'react'

/**
 * A custom React hook that manages state synchronized with the browser's localStorage.
 * It also listens to the 'storage' event to keep state in sync across multiple browser tabs.
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void] {
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') {
            return initialValue
        }
        try {
            const item = window.localStorage.getItem(key)
            return item ? JSON.parse(item) : initialValue
        } catch (error) {
            console.warn(`Error reading localStorage key "${key}":`, error)
            return initialValue
        }
    })

    const setValue = (value: T | ((val: T) => T)) => {
        setStoredValue((prev) => {
            try {
                const valueToStore = value instanceof Function ? value(prev) : value
                if (typeof window !== 'undefined') {
                    window.localStorage.setItem(key, JSON.stringify(valueToStore))
                }
                return valueToStore
            } catch (error) {
                console.warn(`Error setting localStorage key "${key}":`, error)
                return prev
            }
        })
    }

    // Listen to changes from other tabs/windows
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === key && e.newValue) {
                try {
                    setStoredValue(JSON.parse(e.newValue))
                } catch {
                    // ignore parsing error
                }
            }
        }
        window.addEventListener('storage', handleStorageChange)
        return () => window.removeEventListener('storage', handleStorageChange)
    }, [key])

    return [storedValue, setValue]
}

import { useEffect, useState } from "react";
import { useUser } from "../auth/hooks";

// Module-level cache to store full user data keyed by user ID
const userCache = new Map<string | number, any>();
const fetchPromiseCache = new Map<string | number, Promise<any>>();

export function useFullUser() {
  const authUser = useUser();
  const [fullUser, setFullUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // If no authenticated user, clear state and return
    if (!authUser || !authUser.id) {
      setFullUser(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    const userId = authUser.id;

    // Check if we have cached data for this user
    if (userCache.has(userId)) {
      setFullUser(userCache.get(userId));
      setIsLoading(false);
      setError(null);
      return;
    }

    // Check if there's already a fetch in progress for this user
    if (fetchPromiseCache.has(userId)) {
      setIsLoading(true);
      fetchPromiseCache.get(userId)!
        .then((data) => {
          setFullUser(data);
          setError(null);
        })
        .catch((err) => {
          setError(err);
        })
        .finally(() => {
          setIsLoading(false);
        });
      return;
    }

    // No cache and no fetch in progress - start a new fetch
    const controller = new AbortController();
    const { signal } = controller;

    setIsLoading(true);
    const fetchPromise = fetch("/api/users/me/", { signal })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch user");
        return res.json();
      })
      .then((data) => {
        // Cache the successful result
        userCache.set(userId, data);
        fetchPromiseCache.delete(userId);
        return data;
      })
      .catch((err) => {
        fetchPromiseCache.delete(userId);
        if (err.name !== "AbortError") {
          throw err;
        }
        return null;
      });

    // Store the promise so other components can wait on the same fetch
    fetchPromiseCache.set(userId, fetchPromise);

    fetchPromise
      .then((data) => {
        if (data) {
          setFullUser(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(err);
        }
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => controller.abort();
  }, [authUser?.id]);

  return { user: fullUser, isLoading };
}

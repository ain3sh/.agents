# Better Alternatives to useEffect

## 1. Calculate During Render (Derived State)

```tsx
function Form() {
  const [firstName, setFirstName] = useState('Taylor');
  const [lastName, setLastName] = useState('Swift');
  const fullName = firstName + ' ' + lastName; // just compute it
  const isValid = firstName.length > 0 && lastName.length > 0;
}
```

## 2. useMemo for Expensive Calculations

```tsx
function TodoList({ todos, filter }) {
  const visibleTodos = useMemo(
    () => getFilteredTodos(todos, filter),
    [todos, filter]
  );
}
```

If > 1ms in `console.time`, consider memoizing. React Compiler can auto-memoize, reducing manual needs.

## 3. Key Prop to Reset State

```tsx
function ProfilePage({ userId }) {
  return <Profile userId={userId} key={userId} />;
}
function Profile({ userId }) {
  const [comment, setComment] = useState(''); // resets when userId changes
}
```

## 4. Store ID Instead of Object

```tsx
// BAD: Need Effect to "adjust" selection when items change
const [selection, setSelection] = useState(null);
useEffect(() => { setSelection(null); }, [items]);

// GOOD: Derive from ID
const [selectedId, setSelectedId] = useState(null);
const selection = items.find(item => item.id === selectedId) ?? null;
```

## 5. Event Handlers for User Actions

```tsx
function ProductPage({ product, addToCart }) {
  function handleBuyClick() {
    addToCart(product);
    showNotification(`Added ${product.name}!`);
    analytics.track('product_added', { id: product.id });
  }
}
```

Shared logic? Extract a function, call from both handlers.

## 6. useSyncExternalStore for External Stores

```tsx
import { useSyncExternalStore } from 'react';

function subscribe(callback) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function useOnlineStatus() {
  return useSyncExternalStore(
    subscribe,
    () => navigator.onLine,    // client value
    () => true                 // server value (SSR)
  );
}
```

## 7. Lifting State Up

When two components need synchronized state, lift it to common ancestor:

```tsx
function Parent() {
  const [value, setValue] = useState('');
  return (
    <>
      <Input value={value} onChange={setValue} />
      <Preview value={value} />
    </>
  );
}
```

## 8. Custom Hooks for Data Fetching

```tsx
function useData(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    fetch(url)
      .then(res => res.json())
      .then(json => { if (!ignore) { setData(json); setError(null); } })
      .catch(err => { if (!ignore) setError(err); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [url]);

  return { data, error, loading };
}
```

Better: use framework's data fetching (React Query, SWR, Next.js, etc.)

## Summary

| Need | Solution |
|------|----------|
| Value from props/state | Calculate during render |
| Expensive calculation | `useMemo` |
| Reset all state on prop change | `key` prop |
| Respond to user action | Event handler |
| Sync with external system | `useEffect` with cleanup |
| Subscribe to external store | `useSyncExternalStore` |
| Share state between components | Lift state up |
| Fetch data | Custom hook with cleanup / framework |

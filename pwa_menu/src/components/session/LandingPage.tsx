import { useState, useActionState, Suspense, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BranchHeader } from './BranchHeader';
import { NameInput } from './NameInput';
import { ColorPalette } from './ColorPalette';
import { JoinButton } from './JoinButton';
import { Skeleton } from '@/components/ui/Skeleton';
import { joinSession } from '@/services/session.service';
import {
  useSessionStore,
  selectJoinAction,
} from '@/stores/session.store';
import {
  useUiStore,
  selectAddToastAction,
} from '@/stores/ui.store';
import {
  pickRandomAvatarColor,
  type AvatarColor,
} from '@/config/constants';
import i18n from '@/i18n';
import { humanizeSlug } from '@/lib/text';
import { persistLastTableContext } from '@/lib/session-context';

interface JoinFormState {
  error: string | null;
}

/**
 * Landing page — entry point for the QR scan flow.
 *
 * Route params: /:tenant/:branch/mesa/:table
 *
 * Form uses React 19 useActionState pattern.
 * On success: stores session in Zustand + navigates to menu.
 * On error: shows toast.
 */
export default function LandingPage() {
  const { t } = useTranslation('session');
  const navigate = useNavigate();
  const params = useParams<{ tenant: string; branch: string; table: string }>();

  const joinStore = useSessionStore(selectJoinAction);
  const addToast = useUiStore(selectAddToastAction);

  // Local form state — name and selected color
  const [name, setName] = useState('');
  const [selectedColor, setSelectedColor] = useState<AvatarColor>(
    pickRandomAvatarColor()
  );

  async function joinAction(
    _prevState: JoinFormState,
    formData: FormData
  ): Promise<JoinFormState> {
    const branchSlug = params.branch;
    const tableIdentifier = params.table;

    if (!branchSlug || !tableIdentifier) {
      const msg = t('errors.invalidQR');
      addToast(msg, 'error');
      return { error: msg };
    }

    // Read form values from FormData (React 19 pattern)
    const rawName = (formData.get('displayName') as string | null) ?? '';
    const displayName = rawName.trim() || t('landing.anonymous');

    try {
      const avatarColor = (formData.get('avatarColor') as string | null) ?? selectedColor;
      const response = await joinSession({
        branchSlug,
        tableIdentifier,
        displayName,
        avatarColor,
        locale: i18n.language,
      });

      joinStore(response, displayName, selectedColor);
      navigate(`/${params.tenant}/${params.branch}`, { replace: true });
      return { error: null };
    } catch (err: unknown) {
      let message = t('errors.joinFailed');

      if (
        err &&
        typeof err === 'object' &&
        'response' in err
      ) {
        const axiosErr = err as { response?: { status?: number } };
        if (axiosErr.response?.status === 404) {
          message = t('errors.branchNotFound');
        } else if (axiosErr.response?.status === 409) {
          message = t('errors.tableInactive');
        }
      }

      addToast(message, 'error');
      return { error: message };
    }
  }

  const [, formAction, isPending] = useActionState(joinAction, { error: null });

  // Derive branch info from params for header (pre-session, no store data yet)
  const branchName = params.branch ?? '';
  const tableName = params.table ?? '';

  useEffect(() => {
    if (params.tenant && params.branch && params.table) {
      persistLastTableContext({
        tenant: params.tenant,
        branch: params.branch,
        table: params.table,
      });
    }

    const appName = i18n.t('app.name', { ns: 'common' });
    const resolvedBranchName = branchName ? humanizeSlug(branchName) : appName;
    const resolvedTableName = tableName ? humanizeSlug(tableName) : '';
    const title = resolvedTableName
      ? `${resolvedBranchName} · ${resolvedTableName} | ${appName}`
      : `${resolvedBranchName} | ${appName}`;

    document.title = title;

    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.setAttribute(
        'content',
        resolvedTableName
          ? t('meta.descriptionWithTable', { branchName: resolvedBranchName, tableName: resolvedTableName })
          : t('meta.description', { branchName: resolvedBranchName })
      );
    }
  }, [branchName, params.branch, params.table, params.tenant, tableName, t]);

  return (
    <div className="mx-auto w-full max-w-sm px-4 py-8">
      <Suspense fallback={<Skeleton className="h-24 w-full rounded-lg" />}>
        <div className="flex flex-col gap-6">
          <BranchHeader
            branchName={branchName}
            tableName={tableName}
            logoUrl={null}
          />

          <form action={formAction} className="flex flex-col gap-5">
            {/* Hidden inputs expose controlled state to FormData (React 19 pattern) */}
            <input type="hidden" name="displayName" value={name} />
            <input type="hidden" name="avatarColor" value={selectedColor} />

            <NameInput value={name} onChange={setName} />

            <ColorPalette
              selectedColor={selectedColor}
              onSelect={setSelectedColor}
            />

            <JoinButton isLoading={isPending} />
          </form>
        </div>
      </Suspense>
    </div>
  );
}

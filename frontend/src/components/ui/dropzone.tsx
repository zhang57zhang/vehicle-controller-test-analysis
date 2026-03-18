import * as React from "react"
import { UploadCloud } from "lucide-react"
import { cn } from "@/utils/lib"

interface DropzoneProps extends React.HTMLAttributes<HTMLDivElement> {
  onFilesSelected: (files: FileList) => void
  accept?: string
  disabled?: boolean
}

const Dropzone = React.forwardRef<HTMLDivElement, DropzoneProps>(
  ({ className, onFilesSelected, accept, disabled, children, ...props }, ref) => {
    const [isDragging, setIsDragging] = React.useState(false)

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault()
      if (!disabled) {
        setIsDragging(true)
      }
    }

    const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
    }

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      if (!disabled && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onFilesSelected(e.dataTransfer.files)
      }
    }

    const handleClick = () => {
      if (!disabled) {
        const input = document.createElement("input")
        input.type = "file"
        input.multiple = true
        if (accept) {
          input.accept = accept
        }
        input.onchange = (e) => {
          const files = (e.target as HTMLInputElement).files
          if (files && files.length > 0) {
            onFilesSelected(files)
          }
        }
        input.click()
      }
    }

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          isDragging && "border-primary bg-primary/5",
          disabled && "cursor-not-allowed opacity-50",
          !disabled && "cursor-pointer hover:bg-accent",
          className
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        {...props}
      >
        {children || (
          <>
            <UploadCloud className="h-10 w-10 text-muted-foreground" />
            <div className="text-sm">
              <p className="font-medium">点击或拖拽文件到此区域上传</p>
              <p className="text-muted-foreground">
                {accept ? `支持格式：${accept.split(',').join(', ')}` : '支持多种文件格式'}
              </p>
            </div>
          </>
        )}
      </div>
    )
  }
)
Dropzone.displayName = "Dropzone"

export { Dropzone }
